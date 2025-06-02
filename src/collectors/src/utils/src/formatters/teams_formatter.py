import logging
from typing import Dict, Any, List

# Configure logging rajesh 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TeamsFormatter:
    """Formats collected data into Microsoft Teams messages"""
    
    def __init__(self, team_name: str):
        """
        Initialize the Teams formatter
        
        Args:
            team_name: Name of the team
        """
        self.team_name = team_name
    
    def format_daily_digest(self, data: Dict[str, Any], ai_summary: str) -> Dict:
        """
        Format a comprehensive daily digest for Teams
        
        Args:
            data: Dictionary containing all collected data
            ai_summary: AI-generated summary text
            
        Returns:
            Formatted Teams card as a dictionary
        """
        # Create the base card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.2"
                    }
                }
            ]
        }
        
        # Add header
        card["attachments"][0]["content"]["body"].append({
            "type": "TextBlock",
            "text": f"🌅 Good morning, {self.team_name}!",
            "weight": "Bolder",
            "size": "Large",
            "wrap": True
        })
        
        card["attachments"][0]["content"]["body"].append({
            "type": "TextBlock",
            "text": "Here's your daily project digest:",
            "wrap": True
        })
        
        # Add AI Summary section
        if ai_summary:
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": "💡 AI Summary",
                "weight": "Bolder",
                "size": "Medium",
                "spacing": "Medium"
            })
            
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": ai_summary,
                "wrap": True
            })
        
        # Add Jira section if data exists
        jira_data = data.get("jira", {})
        if jira_data and any(jira_data.values()):
            self._add_jira_section(card, jira_data)
        
        # Add GitHub section if data exists
        github_data = data.get("github", {})
        if github_data and any(github_data.values()):
            self._add_github_section(card, github_data)
            
            # Add PR analyses if they exist (NEW SECTION)
            if "pr_analyses" in github_data and github_data["pr_analyses"]:
                self._add_pr_analyses_section(card, github_data["pr_analyses"])
        
        # Add database insights if they exist (NEW SECTION)
        db_data = data.get("database", {})
        if db_data and any(db_data.values()):
            self._add_database_section(card, db_data)
        
        # If no data was found
        if (not jira_data or not any(jira_data.values())) and (not github_data or not any(github_data.values())):
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": "No updates found for today. It's a quiet day! 😊",
                "wrap": True,
                "spacing": "Medium"
            })
        
        return card
    
    def _add_jira_section(self, card: Dict[str, Any], jira_data: Dict[str, Any]):
        """Add Jira data to the Teams card"""
        body = card["attachments"][0]["content"]["body"]
        
        # Add section header
        body.append({
            "type": "TextBlock",
            "text": "🧩 Jira Updates",
            "weight": "Bolder",
            "size": "Medium",
            "spacing": "Medium"
        })
        
        # Add new tickets info
        new_tickets = jira_data.get("new_tickets", [])
        if new_tickets:
            body.append({
                "type": "TextBlock",
                "text": f"📥 {len(new_tickets)} new tickets were created yesterday:",
                "wrap": True
            })
            
            # Add ticket details (limited to 5)
            for ticket in new_tickets[:5]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {ticket['key']}: {ticket['summary']} ({ticket['status']})",
                    "wrap": True
                })
            
            if len(new_tickets) > 5:
                body.append({
                    "type": "TextBlock",
                    "text": f"...and {len(new_tickets) - 5} more new tickets",
                    "isSubtle": True,
                    "wrap": True
                })
        else:
            body.append({
                "type": "TextBlock", 
                "text": "No new tickets created yesterday.",
                "wrap": True
            })
        
        # Add blocked tasks
        blocked_tasks = jira_data.get("blocked_tasks", [])
        if blocked_tasks:
            body.append({
                "type": "TextBlock",
                "text": f"⚠️ {len(blocked_tasks)} tasks are currently blocked:",
                "wrap": True,
                "spacing": "Medium"
            })
            
            # Add blocked task details (limited to 5)
            for task in blocked_tasks[:5]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {task['key']}: {task['summary']} (Assigned to: {task['assignee']})",
                    "wrap": True
                })
            
            if len(blocked_tasks) > 5:
                body.append({
                    "type": "TextBlock",
                    "text": f"...and {len(blocked_tasks) - 5} more blocked tasks",
                    "isSubtle": True,
                    "wrap": True
                })
        
        # Add recently completed tasks
        status_changes = jira_data.get("status_changes", [])
        completed = []
        if status_changes:
            for change in status_changes:
                for sc in change.get("status_changes", []):
                    if sc.get("to") in ["Done", "Closed", "Resolved"]:
                        completed.append({
                            "key": change["key"],
                            "summary": change["summary"],
                            "author": sc["author"],
                            "time": sc["time"]
                        })
            
            if completed:
                body.append({
                    "type": "TextBlock",
                    "text": f"✅ {len(completed)} tasks were completed yesterday:",
                    "wrap": True,
                    "spacing": "Medium"
                })
                
                # Add completed task details (limited to 5)
                for task in completed[:5]:
                    body.append({
                        "type": "TextBlock",
                        "text": f"• {task['key']}: {task['summary']} (by {task['author']})",
                        "wrap": True
                    })
                
                if len(completed) > 5:
                    body.append({
                        "type": "TextBlock",
                        "text": f"...and {len(completed) - 5} more completed tasks",
                        "isSubtle": True,
                        "wrap": True
                    })
    
    def _add_github_section(self, card: Dict[str, Any], github_data: Dict[str, Any]):
        """Add GitHub data to the Teams card"""
        body = card["attachments"][0]["content"]["body"]
        
        # Add section header
        body.append({
            "type": "TextBlock",
            "text": "🛠️ GitHub Activity",
            "weight": "Bolder",
            "size": "Medium",
            "spacing": "Medium"
        })
        
        # Add open PRs info
        open_prs = github_data.get("open_prs", [])
        if open_prs:
            body.append({
                "type": "TextBlock",
                "text": f"🔄 {len(open_prs)} open pull requests waiting for review:",
                "wrap": True
            })
            
            # Add PR details (limited to 5)
            for pr in open_prs[:5]:
                reviewer_text = ""
                if pr.get("reviewers"):
                    reviewer_text = f" (Reviewers: {', '.join(pr['reviewers'][:2])})"
                    if len(pr['reviewers']) > 2:
                        reviewer_text += f" +{len(pr['reviewers']) - 2} more"
                
                body.append({
                    "type": "TextBlock",
                    "text": f"• #{pr['number']}: {pr['title']} by {pr['author']}{reviewer_text}",
                    "wrap": True
                })
            
            if len(open_prs) > 5:
                body.append({
                    "type": "TextBlock",
                    "text": f"...and {len(open_prs) - 5} more open PRs",
                    "isSubtle": True,
                    "wrap": True
                })
        else:
            body.append({
                "type": "TextBlock",
                "text": "No open pull requests waiting for review.",
                "wrap": True
            })
        
        # Add recent merges
        recent_merges = github_data.get("recent_merges", [])
        if recent_merges:
            body.append({
                "type": "TextBlock",
                "text": f"✅ {len(recent_merges)} pull requests were merged yesterday:",
                "wrap": True,
                "spacing": "Medium"
            })
            
            # Add merge details (limited to 5)
            for pr in recent_merges[:5]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• #{pr['number']}: {pr['title']} by {pr['author']}",
                    "wrap": True
                })
            
            if len(recent_merges) > 5:
                body.append({
                    "type": "TextBlock",
                    "text": f"...and {len(recent_merges) - 5} more merged PRs",
                    "isSubtle": True,
                    "wrap": True
                })
        
        # Add urgent commits
        urgent_commits = github_data.get("urgent_commits", [])
        if urgent_commits:
            body.append({
                "type": "TextBlock",
                "text": f"🚨 {len(urgent_commits)} urgent commits detected yesterday:",
                "wrap": True,
                "spacing": "Medium"
            })
            
            # Add commit details (limited to 5)
            for commit in urgent_commits[:5]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {commit['sha']}: {commit['message']} by {commit['author']}",
                    "wrap": True
                })
            
            if len(urgent_commits) > 5:
                body.append({
                    "type": "TextBlock",
                    "text": f"...and {len(urgent_commits) - 5} more urgent commits",
                    "isSubtle": True,
                    "wrap": True
                })
    
    # NEW METHOD: Add PR analyses section
    def _add_pr_analyses_section(self, card: Dict[str, Any], pr_analyses: List[Dict[str, Any]]):
        """Add PR analyses to the Teams card"""
        body = card["attachments"][0]["content"]["body"]
        
        # Add section header
        body.append({
            "type": "TextBlock",
            "text": "🔍 Pull Request Analyses",
            "weight": "Bolder",
            "size": "Medium",
            "spacing": "Medium"
        })
        
        if not pr_analyses:
            body.append({
                "type": "TextBlock",
                "text": "No PR analyses available.",
                "wrap": True
            })
            return
        
        # Add each PR analysis (limited to 3 to keep the card manageable)
        for analysis in pr_analyses[:3]:
            pr_number = analysis.get("pr_number")
            repo = analysis.get("repo", "")
            title = analysis.get("title", "Untitled PR")
            author = analysis.get("author", "Unknown")
            analysis_text = analysis.get("analysis", "No analysis available")
            url = analysis.get("url", "")
            
            # Add PR title and info
            body.append({
                "type": "TextBlock",
                "text": f"**PR #{pr_number}: {title}**",
                "weight": "Bolder",
                "wrap": True,
                "spacing": "Medium"
            })
            
            body.append({
                "type": "TextBlock", 
                "text": f"Repository: {repo} | Author: {author}",
                "isSubtle": True,
                "wrap": True
            })
            
            # Add separator
            body.append({
                "type": "TextBlock",
                "text": "---",
                "wrap": True
            })
            
            # Add analysis content - make it collapsible if it's long
            if len(analysis_text) > 500:
                # Summary version
                body.append({
                    "type": "TextBlock",
                    "text": analysis_text[:500] + "...",
                    "wrap": True
                })
            else:
                body.append({
                    "type": "TextBlock",
                    "text": analysis_text,
                    "wrap": True
                })
            
            # Add action button to view PR if URL is available
            if url:
                body.append({
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Pull Request",
                            "url": url
                        }
                    ]
                })
        
        # Add note about limited analyses
        if len(pr_analyses) > 3:
            body.append({
                "type": "TextBlock",
                "text": f"...and {len(pr_analyses) - 3} more PR analyses",
                "isSubtle": True,
                "wrap": True,
                "spacing": "Small"
            })
    
    # NEW METHOD: Add database insights section
    def _add_database_section(self, card: Dict[str, Any], db_data: Dict[str, Any]):
        """Add database insights to the Teams card"""
        body = card["attachments"][0]["content"]["body"]
        
        # Check if there are activity stats to display
        activity_stats = db_data.get("activity_stats", {})
        if not activity_stats:
            return
        
        # Add section header
        body.append({
            "type": "TextBlock",
            "text": "📊 Weekly Database Insights",
            "weight": "Bolder",
            "size": "Medium",
            "spacing": "Medium"
        })
        
        # Add weekly stats
        weekly_stats_text = f"• {activity_stats.get('weekly_prs', 0)} PRs this week\n"
        weekly_stats_text += f"• {activity_stats.get('weekly_tickets', 0)} tickets created\n"
        weekly_stats_text += f"• {activity_stats.get('weekly_completed', 0)} tickets completed\n"
        
        body.append({
            "type": "TextBlock",
            "text": weekly_stats_text,
            "wrap": True
        })
        
        # Add team metrics if available
        team_metrics = db_data.get("team_metrics", {})
        if team_metrics:
            body.append({
                "type": "TextBlock",
                "text": f"Team size: {team_metrics.get('member_count', 0)} members | {team_metrics.get('github_users', 0)} using GitHub",
                "wrap": True,
                "isSubtle": True
            })
