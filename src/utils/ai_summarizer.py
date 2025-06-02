import logging
import json
import os
import boto3
from typing import Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BedrockSummarizer:
    """Uses Amazon Bedrock's Claude model to generate summaries"""
    
    def __init__(self):
        """Initialize Bedrock client"""
        # Load environment variables if not already loaded
        load_dotenv()
        
        self.aws_region = os.getenv("AWS_REGION")
        self.model_id = os.getenv("BEDROCK_MODEL_ID")
        self.max_tokens = 1000
        
        self.client = None
        try:
            # Initialize Bedrock client with credentials
            session = boto3.Session(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                region_name=self.aws_region
            )
            
            self.client = session.client('bedrock-runtime')
            logger.info("Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
    
    def generate_summary(self, data: Dict[str, Any], team_name: str) -> str:
        """
        Generate a summary of the collected data using Bedrock's Claude model
        
        Args:
            data: Dictionary containing the collected data
            team_name: Name of the team
        
        Returns:
            AI-generated summary text
        """
        if not self.client or not self.model_id:
            logger.error("Bedrock client not initialized or model ID not provided")
            return "Unable to generate AI summary due to configuration issues."
        
        # Create the prompt for Claude
        prompt = self._create_prompt(data, team_name)
        logger.debug(f"Generated prompt for AI summary: {prompt}")
        
        try:
            # Create request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response.get('body').read())
            summary = response_body.get('content', [{}])[0].get('text', '')
            
            logger.info("Successfully generated AI summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary with Bedrock: {str(e)}")
            return f"Unable to generate AI summary. Error: {str(e)}"
    
    def _create_prompt(self, data: Dict[str, Any], team_name: str) -> str:
        """
        Create a prompt for the AI model based on the collected data
        
        Args:
            data: Dictionary containing the collected data
            team_name: Name of the team
        
        Returns:
            Formatted prompt string
        """
        # Extract data for the prompt
        jira_data = data.get('jira', {})
        github_data = data.get('github', {})
        
        # Format Jira data
        jira_section = self._format_jira_for_prompt(jira_data)
        
        # Format GitHub data
        github_section = self._format_github_for_prompt(github_data)
        
        # Create the complete prompt
        prompt = f"""
You are a helpful assistant for the {team_name} team. Your task is to create a concise, informative daily update based on the data below.
Focus on actionable insights and highlight the most important issues that need attention. Also mention any positive accomplishments.

===== JIRA DATA =====
{jira_section}

===== GITHUB DATA =====
{github_section}

Based on this data, please provide:
1. A brief summary (2-3 sentences) highlighting the most important information
2. Key observations about current status and blockers
3. Any connections between different issues (e.g., if GitHub commits relate to Jira tickets)
4. Suggested priorities or actions for the team

Your response should be professional but friendly in tone, around 150-200 words total.
"""
        return prompt
    
    def _format_jira_for_prompt(self, jira_data: Dict[str, Any]) -> str:
        """Format Jira data for the prompt"""
        sections = []
        
        # New tickets
        new_tickets = jira_data.get('new_tickets', [])
        if new_tickets:
            sections.append(f"NEW TICKETS ({len(new_tickets)}):")
            for ticket in new_tickets[:5]:  # Limit to 5
                sections.append(f"- {ticket['key']}: {ticket['summary']} ({ticket['status']})")
            if len(new_tickets) > 5:
                sections.append(f"- Plus {len(new_tickets) - 5} more new tickets")
        else:
            sections.append("NEW TICKETS: None in the last 24 hours")
        
        # Status changes
        status_changes = jira_data.get('status_changes', [])
        if status_changes:
            sections.append(f"\nSTATUS CHANGES ({len(status_changes)}):")
            for change in status_changes[:5]:  # Limit to 5
                last_change = change['status_changes'][-1]
                sections.append(f"- {change['key']}: Changed from '{last_change['from']}' to '{last_change['to']}' by {last_change['author']}")
            if len(status_changes) > 5:
                sections.append(f"- Plus {len(status_changes) - 5} more status changes")
        else:
            sections.append("\nSTATUS CHANGES: None in the last 24 hours")
        
        # Blocked tasks
        blocked_tasks = jira_data.get('blocked_tasks', [])
        if blocked_tasks:
            sections.append(f"\nBLOCKED TASKS ({len(blocked_tasks)}):")
            for task in blocked_tasks[:5]:  # Limit to 5
                sections.append(f"- {task['key']}: {task['summary']} (Assigned to: {task['assignee']})")
            if len(blocked_tasks) > 5:
                sections.append(f"- Plus {len(blocked_tasks) - 5} more blocked tasks")
        else:
            sections.append("\nBLOCKED TASKS: None currently")
        
        return "\n".join(sections)
    
    def _format_github_for_prompt(self, github_data: Dict[str, Any]) -> str:
        """Format GitHub data for the prompt"""
        sections = []
        
        # Open PRs
        open_prs = github_data.get('open_prs', [])
        if open_prs:
            sections.append(f"OPEN PULL REQUESTS ({len(open_prs)}):")
            for pr in open_prs[:5]:  # Limit to 5
                sections.append(f"- #{pr['number']} {pr['title']} by {pr['author']} ({pr['days_open']} days open)")
            if len(open_prs) > 5:
                sections.append(f"- Plus {len(open_prs) - 5} more open PRs")
        else:
            sections.append("OPEN PULL REQUESTS: None currently")
        
        # Recent merges
        recent_merges = github_data.get('recent_merges', [])
        if recent_merges:
            sections.append(f"\nRECENT MERGES ({len(recent_merges)}):")
            for pr in recent_merges[:5]:  # Limit to 5
                sections.append(f"- #{pr['number']} {pr['title']} by {pr['author']}")
            if len(recent_merges) > 5:
                sections.append(f"- Plus {len(recent_merges) - 5} more recent merges")
        else:
            sections.append("\nRECENT MERGES: None in the last 24 hours")
        
        # Urgent commits
        urgent_commits = github_data.get('urgent_commits', [])
        if urgent_commits:
            sections.append(f"\nURGENT COMMITS ({len(urgent_commits)}):")
            for commit in urgent_commits[:5]:  # Limit to 5
                sections.append(f"- {commit['sha']} {commit['message']} by {commit['author']}")
            if len(urgent_commits) > 5:
                sections.append(f"- Plus {len(urgent_commits) - 5} more urgent commits")
        else:
            sections.append("\nURGENT COMMITS: None in the last 24 hours")
        
        return "\n".join(sections)
    
    def analyze_pr_diff(self, diff_data: Dict[str, Any]) -> str:
        """
        Analyze a PR diff using AI
        Args:
            diff_data: Dictionary with PR diff information
        Returns:
            AI-generated analysis text
        """
        # Build prompt similar to what's in github_collector.py
        prompt = self._build_pr_analysis_prompt(diff_data)
        
        # Use the custom text generation method
        return self.generate_custom_text(prompt)
    
    def _build_pr_analysis_prompt(self, diff_data: Dict[str, Any]) -> str:
        """Build a prompt for PR analysis"""
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
        
        return prompt

    def generate_custom_text(self, prompt: str) -> str:
        """
        Generate custom text based on the given prompt
        Args:
            prompt: The prompt to send to the AI model
        Returns:
            AI-generated text
        """
        if not self.client or not self.model_id:
            logger.error("Bedrock client not initialized or model ID not provided")
            return "Unable to generate text due to configuration issues."
        
        try:
            # Create request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response.get('body').read())
            generated_text = response_body.get('content', [{}])[0].get('text', '')
            
            logger.info("Successfully generated text with AI")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating text with Bedrock: {str(e)}")
            return f"Unable to generate text. Error: {str(e)}"

    # Alternative method for environments where Bedrock may not be accessible
    def generate_simple_summary(self, data: Dict[str, Any], team_name: str) -> str:
        """
        Generate a simple summary without using the AI model
        This is a fallback in case Bedrock is not accessible
        
        Args:
            data: Dictionary containing the collected data
            team_name: Name of the team
            
        Returns:
            A simple summary based on counts and status
        """
        summary_parts = []
        
        # Get counts from Jira
        jira_data = data.get('jira', {})
        new_tickets_count = len(jira_data.get('new_tickets', []))
        blocked_tasks_count = len(jira_data.get('blocked_tasks', []))
        
        # Get counts from GitHub
        github_data = data.get('github', {})
        open_prs_count = len(github_data.get('open_prs', []))
        merged_prs_count = len(github_data.get('recent_merges', []))
        urgent_commits_count = len(github_data.get('urgent_commits', []))
        
        # Build summary
        if new_tickets_count > 0:
            summary_parts.append(f"{new_tickets_count} new Jira tickets were created")
        
        if blocked_tasks_count > 0:
            summary_parts.append(f"{blocked_tasks_count} tasks are currently blocked")
        
        if open_prs_count > 0:
            summary_parts.append(f"{open_prs_count} pull requests are waiting for review")
        
        if merged_prs_count > 0:
            summary_parts.append(f"{merged_prs_count} pull requests were merged yesterday")
        
        if urgent_commits_count > 0:
            summary_parts.append(f"{urgent_commits_count} urgent commits were made yesterday")
        
        if not summary_parts:
            return f"Good morning, {team_name}! No significant updates or issues to report today. Everything appears to be running smoothly."
        
        # Combine the summary parts
        summary = f"Here's today's update for {team_name}: " + ", ".join(summary_parts[:-1])
        if len(summary_parts) > 1:
            summary += f", and {summary_parts[-1]}."
        else:
            summary += f" {summary_parts[0]}."
            
        # Add a priority statement
        if blocked_tasks_count > 0:
            summary += f" Priority should be given to resolving the {blocked_tasks_count} blocked tasks."
        elif open_prs_count > 0:
            summary += f" Consider reviewing the open pull requests to keep development moving forward."
        
        return summary
