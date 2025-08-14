"""GitHub integration service."""

import time
import random
from typing import Optional, Dict, Any
from pathlib import Path

import requests
import structlog

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)


class GitHubService:
    """GitHub API integration service."""
    
    def __init__(self):
        """Initialize GitHub service."""
        self.token = settings.GITHUB_TOKEN
        self.org = getattr(settings, 'GITHUB_ORG', None)
        self.base_url = "https://api.github.com"
        
        if not self.token or self.token in ["your-github-token-here", "xoxb-your-github-token"]:
            raise ValueError("GitHub token is not configured properly")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with GitHub API."""
        try:
            # Test authentication by getting user info
            response = self._make_request("GET", "/user")
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info("GitHub API authentication successful", user=user_info.get('login'))
            else:
                raise requests.HTTPError(f"Authentication failed: {response.status_code}")
                
        except Exception as e:
            logger.error("GitHub API authentication failed", error=str(e))
            raise ExternalServiceError(f"GitHub authentication failed: {e}")
    
    def create_repository(
        self, 
        name: str, 
        description: str = "",
        private: bool = False,
        auto_init: bool = True
    ) -> Optional[str]:
        """Create a new repository."""
        return self._execute_with_retry(
            self._create_repository_impl, 
            name, description, private, auto_init
        )
    
    def _create_repository_impl(
        self, 
        name: str, 
        description: str = "",
        private: bool = False,
        auto_init: bool = True
    ) -> Optional[str]:
        """Implementation of repository creation."""
        logger.info("Creating GitHub repository", name=name)
        
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "gitignore_template": "Python",  # Default template
            "license_template": "mit"  # Default license
        }
        
        # Create in organization if specified
        endpoint = f"/orgs/{self.org}/repos" if self.org else "/user/repos"
        
        try:
            response = self._make_request("POST", endpoint, json=payload)
            
            if response.status_code == 201:
                repo_data = response.json()
                repo_url = repo_data.get('html_url')
                
                logger.info("Repository created successfully", 
                           name=name, url=repo_url)
                return repo_url
            else:
                logger.error("Failed to create repository", 
                           name=name, status=response.status_code, 
                           response=response.text)
                return None
                
        except requests.RequestException as e:
            logger.error("Repository creation request failed", 
                        name=name, error=str(e))
            return None
    
    def repository_exists(self, name: str) -> bool:
        """Check if repository exists."""
        try:
            owner = self.org if self.org else self._get_authenticated_user()
            endpoint = f"/repos/{owner}/{name}"
            
            response = self._make_request("GET", endpoint)
            return response.status_code == 200
            
        except Exception as e:
            logger.error("Failed to check repository existence", 
                        name=name, error=str(e))
            return False
    
    def get_repository_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        try:
            owner = self.org if self.org else self._get_authenticated_user()
            endpoint = f"/repos/{owner}/{name}"
            
            response = self._make_request("GET", endpoint)
            
            if response.status_code == 200:
                repo_data = response.json()
                return {
                    'name': repo_data.get('name'),
                    'full_name': repo_data.get('full_name'),
                    'description': repo_data.get('description'),
                    'html_url': repo_data.get('html_url'),
                    'clone_url': repo_data.get('clone_url'),
                    'ssh_url': repo_data.get('ssh_url'),
                    'private': repo_data.get('private'),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at')
                }
            else:
                logger.warning("Repository not found", name=name)
                return None
                
        except Exception as e:
            logger.error("Failed to get repository info", 
                        name=name, error=str(e))
            return None
    
    def delete_repository(self, name: str) -> bool:
        """Delete a repository (use with caution)."""
        try:
            owner = self.org if self.org else self._get_authenticated_user()
            endpoint = f"/repos/{owner}/{name}"
            
            response = self._make_request("DELETE", endpoint)
            
            if response.status_code == 204:
                logger.info("Repository deleted successfully", name=name)
                return True
            else:
                logger.error("Failed to delete repository", 
                           name=name, status=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Repository deletion failed", 
                        name=name, error=str(e))
            return False
    
    def create_issue(
        self, 
        repo_name: str, 
        title: str, 
        body: str = "",
        labels: list = None
    ) -> Optional[str]:
        """Create an issue in the repository."""
        try:
            owner = self.org if self.org else self._get_authenticated_user()
            endpoint = f"/repos/{owner}/{repo_name}/issues"
            
            payload = {
                "title": title,
                "body": body,
                "labels": labels or []
            }
            
            response = self._make_request("POST", endpoint, json=payload)
            
            if response.status_code == 201:
                issue_data = response.json()
                issue_url = issue_data.get('html_url')
                
                logger.info("Issue created successfully", 
                           repo=repo_name, title=title, url=issue_url)
                return issue_url
            else:
                logger.error("Failed to create issue", 
                           repo=repo_name, title=title, 
                           status=response.status_code)
                return None
                
        except Exception as e:
            logger.error("Issue creation failed", 
                        repo=repo_name, title=title, error=str(e))
            return None
    
    def _get_authenticated_user(self) -> str:
        """Get authenticated user's username."""
        try:
            response = self._make_request("GET", "/user")
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get('login')
            else:
                raise requests.HTTPError("Failed to get authenticated user")
                
        except Exception as e:
            logger.error("Failed to get authenticated user", error=str(e))
            raise
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to GitHub API."""
        url = f"{self.base_url}{endpoint}"
        
        # Add headers to kwargs
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self.headers)
        
        response = requests.request(method, url, **kwargs)
        
        # Log request details
        logger.debug("GitHub API request", 
                    method=method, endpoint=endpoint, 
                    status=response.status_code)
        
        return response
    
    def _execute_with_retry(self, func, *args, max_retries: int = 3, **kwargs):
        """Execute function with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except requests.exceptions.HTTPError as e:
                if self._is_retryable_error(e) and attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("Retrying API call", 
                                 attempt=attempt + 1, wait_time=wait_time)
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("API call failed", error=str(e))
                    raise
                    
            except Exception as e:
                logger.error("Unexpected error", error=str(e))
                raise
    
    def _is_retryable_error(self, error) -> bool:
        """Check if error is retryable."""
        if hasattr(error, 'response') and error.response:
            retryable_codes = {429, 500, 502, 503, 504}
            return error.response.status_code in retryable_codes
        return False
    
    def test_connection(self) -> bool:
        """Test GitHub API connection."""
        try:
            response = self._make_request("GET", "/user")
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info("Connection test successful", 
                           user=user_data.get('login'))
                return True
            else:
                logger.error("Connection test failed", 
                           status=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        try:
            response = self._make_request("GET", "/rate_limit")
            
            if response.status_code == 200:
                rate_limit_data = response.json()
                return rate_limit_data.get('rate', {})
            else:
                logger.error("Failed to get rate limit status", 
                           status=response.status_code)
                return {}
                
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            return {}