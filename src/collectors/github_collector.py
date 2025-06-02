import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from github import Github
from dotenv import load_dotenv
from utils.ai_summarizer import BedrockSummarizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GithubCollector:
    """Collector for GitHub repository data"""
    
    def __init__(self):
        """Initialize GitHub client"""
        # Load environment variables if not already loaded
        load_dotenv()
        
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repos = os.getenv("GITHUB_REPOS", "").split(",")
        self.ai_summarizer = None
        
        self.client = None
        try:
            if self.github_token:
                self.client = Github(self.github_token)
                logger.info("GitHub client initialized successfully")
            else:
                logger.warning("GitHub token not provided. Set GITHUB_TOKEN in .env file.")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
    
    def get_open_prs(self) -> List[Dict[str, Any]]:
        """Get open pull requests waiting for review"""
        if not self.client or not self.repos or self.repos == [""]:
            logger.warning("GitHub client not initialized or no repositories configured")
            return []
        
        open_prs = []
        
        try:
            for repo_name in self.repos:
                repo_name = repo_name.strip()
                if not repo_name:
                    continue
                    
                logger.info(f"Fetching open PRs from {repo_name}")
                repo = self.client.get_repo(repo_name)
                pulls = repo.get_pulls(state='open')
                
                for pr in pulls:
                    # Get reviewers
                    reviewers = []
                    try:
                        review_requests = pr.get_review_requests()
                        reviewers = [reviewer.login for reviewer in review_requests[0]]
                    except Exception as e:
                        logger.debug(f"Could not fetch reviewers for PR #{pr.number}: {str(e)}")
                    
                    pr_data = {
                        "number": pr.number,
                        "title": pr.title,
                        "url": pr.html_url,
                        "author": pr.user.login if pr.user else "Unknown",
                        "created_at": pr.created_at.strftime("%Y-%m-%d"),
                        "days_open": (datetime.now(pr.created_at.tzinfo) - pr.created_at).days,
                        "repository": repo_name,
                        "reviewers": reviewers
                    }
                    open_prs.append(pr_data)
            
            logger.info(f"Found {len(open_prs)} open PRs")
            return open_prs
            
        except Exception as e:
            logger.error(f"Error fetching open PRs: {str(e)}")
            return []
    
    def get_recent_merges(self) -> List[Dict[str, Any]]:
        """Get PRs merged in the last 24 hours"""
        if not self.client or not self.repos or self.repos == [""]:
            logger.warning("GitHub client not initialized or no repositories configured")
            return []
        
        yesterday = datetime.now(datetime.timezone.utc) - timedelta(days=1)
        merged_prs = []
        
        try:
            for repo_name in self.repos:
                repo_name = repo_name.strip()
                if not repo_name:
                    continue
                    
                logger.info(f"Fetching recent merges from {repo_name}")
                repo = self.client.get_repo(repo_name)
                pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
                
                for pr in pulls:
                    if pr.merged and pr.merged_at and pr.merged_at > yesterday:
                        pr_data = {
                            "number": pr.number,
                            "title": pr.title,
                            "url": pr.html_url,
                            "author": pr.user.login if pr.user else "Unknown",
                            "merged_at": pr.merged_at.strftime("%Y-%m-%d %H:%M"),
                            "repository": repo_name,
                            "merged_by": pr.merged_by.login if pr.merged_by else "Unknown"
                        }
                        merged_prs.append(pr_data)
            
            logger.info(f"Found {len(merged_prs)} PRs merged in the last 24 hours")
            return merged_prs
            
        except Exception as e:
            logger.error(f"Error fetching recent merges: {str(e)}")
            return []
    
    def get_urgent_commits(self) -> List[Dict[str, Any]]:
        """Get commits with urgent keywords in the last 24 hours"""
        if not self.client or not self.repos or self.repos == [""]:
            logger.warning("GitHub client not initialized or no repositories configured")
            return []
        
        yesterday = datetime.now() - timedelta(days=1)
        urgent_keywords = ["fix", "hotfix", "urgent", "emergency", "critical", "bug"]
        urgent_commits = []
        
        try:
            for repo_name in self.repos:
                repo_name = repo_name.strip()
                if not repo_name:
                    continue
                    
                logger.info(f"Fetching recent commits from {repo_name}")
                repo = self.client.get_repo(repo_name)
                commits = repo.get_commits(since=yesterday)
                
                for commit in commits:
                    message = commit.commit.message.lower()
                    if any(keyword in message for keyword in urgent_keywords):
                        try:
                            commit_data = {
                                "sha": commit.sha[:7],
                                "message": commit.commit.message.split("\n")[0],  # First line only
                                "url": commit.html_url,
                                "author": commit.author.login if commit.author else commit.commit.author.name,
                                "date": commit.commit.author.date.strftime("%Y-%m-%d %H:%M"),
                                "repository": repo_name
                            }
                            urgent_commits.append(commit_data)
                        except Exception as e:
                            logger.debug(f"Error processing commit {commit.sha}: {str(e)}")
            
            logger.info(f"Found {len(urgent_commits)} urgent commits in the last 24 hours")
            return urgent_commits
            
        except Exception as e:
            logger.error(f"Error fetching urgent commits: {str(e)}")
            return []
            
    def analyze_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Analyze a PR with AI
        Args:
            repo_name: Name of the repository (e.g. 'organization/repo')
            pr_number: PR number to analyze
        Returns:
            Dictionary with PR analysis
        """
        if not self.client:
            logger.warning("GitHub client not initialized")
            return {}
            
        try:
            logger.info(f"Analyzing PR #{pr_number} in {repo_name}")
            
            # Get the PR
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get the diff
            diff_data = {
                "title": pr.title,
                "body": pr.body,
                "user": pr.user.login if pr.user else "Unknown",
                "created_at": pr.created_at.strftime("%Y-%m-%d"),
                "files": []
            }
            
            # Get files changed
            files = pr.get_files()
            for file in files:
                file_data = {
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch  # The actual diff content
                }
                diff_data["files"].append(file_data)
            
            # Create the prompt for AI analysis
            prompt = f"""You are a senior software engineer.
Summarize this pull request in plain English.
Then suggest 3-5 relevant unit test cases based on the logic in the diff.

Pull Request: {diff_data.get('title')}
Author: {diff_data.get('user')}
Description: {diff_data.get('body', 'No description provided.')}

Changed files:
"""

            # Add file changes to prompt
            for file in diff_data.get("files", []):
                prompt += f"\nFile: {file.get('filename')}"
                prompt += f"\nStatus: {file.get('status')}"
                prompt += f"\nChanges: +{file.get('additions')} -{file.get('deletions')} lines"
                
                # Add the patch/diff if it's not too large
                patch = file.get("patch")
                if patch and len(patch) < 3000:  # Limit patch size
                    prompt += f"\n```\n{patch}\n```\n"
                else:
                    prompt += "\n[Diff too large to include]\n"
            
            # Here you would call your AI service to analyze the PR
            # For now, we'll just create a placeholder
            # In a real implementation, you would use BedrockSummarizer or another AI service
            
            # Placeholder for AI analysis result
            #analysis_text = f"PR Analysis for {repo_name}#{pr_number}: {pr.title}\n"
            #analysis_text += "This is a placeholder for AI-generated analysis.\n"
            #analysis_text += "In a real implementation, this would be generated by your AI service.\n\n"
            #analysis_text += "Suggested test cases:\n"
            #analysis_text += "1. Test case for basic functionality\n"
            #analysis_text += "2. Test case for edge conditions\n"
            #analysis_text += "3. Test case for error handling"
            if self.ai_summarizer:
                analysis_text = self.ai_summarizer.analyze_pr_diff(diff_data)
            else:
                # Use placeholder if AI is not available
                analysis_text = f"PR Analysis for {repo_name}#{pr_number}: {pr.title}\n"
                analysis_text += "AI analysis is currently unavailable.\n"
                analysis_text += "Enable AI analysis by setting up AWS Bedrock integration.\n"
            # Save the AI prompt for potential debugging/development
            logger.debug(f"AI Prompt for PR #{pr_number}:\n{prompt}")
            
            return {
                "pr_number": pr_number,
                "repo": repo_name,
                "title": diff_data.get("title"),
                "author": diff_data.get("user"),
                "analysis": analysis_text,
                "url": pr.html_url
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PR {repo_name}#{pr_number}: {str(e)}")
            return {}
    
    def get_pr_analyses(self) -> List[Dict[str, Any]]:
        """Analyze recent or important PRs"""
        if not self.client or not self.repos or self.repos == [""]:
            logger.warning("GitHub client not initialized or no repositories configured")
            return []
            
        analyses = []
        
        try:
            # Get open PRs
            open_prs = self.get_open_prs()
            
            # Analyze up to 3 most recent PRs
            for pr in open_prs[:3]:
                repo_name = pr.get("repository")
                pr_number = pr.get("number")
                
                if repo_name and pr_number:
                    analysis = self.analyze_pr(repo_name, pr_number)
                    if analysis:
                        analyses.append(analysis)
            
            logger.info(f"Generated {len(analyses)} PR analyses")
            return analyses
            
        except Exception as e:
            logger.error(f"Error generating PR analyses: {str(e)}")
            return []
    
    def collect(self) -> Dict[str, Any]:
        """Collect all GitHub data"""
        data = {
            "open_prs": self.get_open_prs(),
            "recent_merges": self.get_recent_merges(),
            "urgent_commits": self.get_urgent_commits()
        }
        
        # Optionally add PR analyses - this might be expensive in terms of API calls and tokens
        # so we'll make it optional based on an environment variable
        if os.getenv("ENABLE_PR_ANALYSIS", "false").lower() == "true":
            data["pr_analyses"] = self.get_pr_analyses()
        
        return data
