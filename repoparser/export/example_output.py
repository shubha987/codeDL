"""
Example Output - Positive Pairs and Triplets

This file shows example output from the pairs_triplets_generator.

POSITIVE PAIRS FORMAT:
Each chunk generates 4-5 question variations, all pointing to the same code.
"""

# Example Positive Pairs (question → code)
POSITIVE_PAIRS_EXAMPLE = [
    # Variation 1
    {
        "id": "pair_0001",
        "global_id": "primary_0a683c5d",
        "anchor": "How to create a WorkFlow class that builds a stateful workflow?",
        "positive": """from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph

from .state import EmailsState
from .nodes import Nodes
from .crew.crew import EmailFilterCrew

class WorkFlow():
    def __init__(self):
        nodes = Nodes()
        workflow = StateGraph(EmailsState)

        workflow.add_node("check_new_emails", nodes.check_email)
        workflow.add_node("wait_next_run", nodes.wait_next_run)
        workflow.add_node("draft_responses", EmailFilterCrew().kickoff)

        workflow.set_entry_point("check_new_emails")
        workflow.add_conditional_edges(
            "check_new_emails",
            nodes.new_emails,
            {
                "continue": 'draft_responses',
                "end": 'wait_next_run'
            }
        )
        workflow.add_edge('draft_responses', 'wait_next_run')
        workflow.add_edge('wait_next_run', 'check_new_emails')
        self.app = workflow.compile()""",
        "metadata": {
            "file_path": "graph.py",
            "chunk_type": "class",
            "symbol_type": "class",
            "language": "python"
        }
    },
    # Variation 2 (same code, different question)
    {
        "id": "pair_0002",
        "global_id": "primary_0a683c5d",
        "anchor": "What is the implementation of WorkFlow?",
        "positive": "... (same code as above)",
        "metadata": {"file_path": "graph.py", "chunk_type": "class"}
    },
    # Variation 3
    {
        "id": "pair_0003",
        "global_id": "primary_0a683c5d", 
        "anchor": "How to define a class for building a stateful workflow?",
        "positive": "... (same code as above)",
        "metadata": {"file_path": "graph.py", "chunk_type": "class"}
    },
    # Variation 4
    {
        "id": "pair_0004",
        "global_id": "primary_0a683c5d",
        "anchor": "Show me how to implement WorkFlow",
        "positive": "... (same code as above)",
        "metadata": {"file_path": "graph.py", "chunk_type": "class"}
    },
    # Variation 5
    {
        "id": "pair_0005",
        "global_id": "primary_0a683c5d",
        "anchor": "What's the code pattern for WorkFlow?",
        "positive": "... (same code as above)",
        "metadata": {"file_path": "graph.py", "chunk_type": "class"}
    }
]


# Example Triplets (anchor=question, positive=relevant, negative=irrelevant)
TRIPLETS_EXAMPLE = [
    {
        "id": "triplet_0001",
        "global_id": "primary_beaa60c6",
        "triplet": [
            # ANCHOR (Query)
            "How to create a reusable prompt template that formats input variables for different tasks?",
            
            # POSITIVE (Relevant implementation)
            """class PromptTemplate(BasePromptTemplate):
    '''Prompt template that formats inputs to language models.
    
    Allows you to create templates with placeholders that get filled
    with dynamic input values for different prompts.
    '''
    
    template: str
    input_variables: List[str]
    validate_template: bool = True
    
    def format(self, **kwargs: Any) -> str:
        '''Format the template with the given input variables.'''
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        return self.template.format(**kwargs)
    
    def format_prompt(self, **kwargs: Any) -> PromptValue:
        '''Format prompt and return PromptValue.'''
        return PromptValue(text=self.format(**kwargs))
""",
            
            # NEGATIVE (Irrelevant - this parses output, not formats input)
            """class OutputParser(BaseOutputParser[T]):
    '''Parse the output of a language model into structured format.
    
    Converts raw LLM text responses into structured Python objects
    like dictionaries, lists, or custom classes.
    '''
    
    @abstractmethod
    def parse(self, text: str) -> T:
        '''Parse text into structured output.'''
        pass
    
    def parse_raw(self, output: str) -> T:
        '''Parse raw output from language model.'''
        return self.parse(output)
"""
        ],
        "metadata": {
            "anchor_file": "prompts/template.py",
            "anchor_type": "class",
            "negative_file": "output_parsers/base.py",
            "negative_type": "class",
            "negative_id": "primary_xyz12345"
        }
    },
    {
        "id": "triplet_0002",
        "global_id": "primary_089433b3",
        "triplet": [
            # ANCHOR (Query about email handling)
            "How to implement a check_email method that searches for new emails?",
            
            # POSITIVE (Email checking implementation)
            """def check_email(self, state):
        print("# Checking for new emails")
        search = GmailSearch(api_resource=self.gmail.api_resource)
        emails = search('after:newer_than:1d')
        checked_emails = state['checked_emails_ids'] if state['checked_emails_ids'] else []
        thread = []
        new_emails = []
        for email in emails:
            if (email['id'] not in checked_emails) and (email['threadId'] not in thread):
                thread.append(email['threadId'])
                new_emails.append({
                    "id": email['id'],
                    "threadId": email['threadId'],
                    "snippet": email['snippet'],
                    "sender": email["sender"]
                })
        return {"emails": new_emails, "checked_emails_ids": checked_emails}""",
            
            # NEGATIVE (Database operation - different domain)
            """def query_database(self, query: str) -> List[Dict]:
        '''Execute SQL query against the database.'''
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in results]"""
        ],
        "metadata": {
            "anchor_file": "nodes.py",
            "anchor_type": "method",
            "negative_file": "database/operations.py",
            "negative_type": "method"
        }
    }
]


# Summary Statistics
EXPECTED_OUTPUT = """
📊 Summary Statistics:
   Total Positive Pairs: 400-500 (100 chunks × 4-5 variance)
   Total Triplets: 100 (no variance)
   
   Output Files:
   - positive_pairs.jsonl  (one pair per line)
   - positive_pairs.json   (array format for inspection)
   - triplets.jsonl        (one triplet per line)
   - triplets.json         (array format with triplet list)

📝 Key Points:
   1. Positive Pairs: anchor=question, positive=code
   2. Triplets: anchor=question, positive=relevant_code, negative=irrelevant_code
   3. Global ID (global_id) links to original chunk_id/document_id
   4. Variance creates 4-5 different questions for the same code
   5. Negatives are semantically different (different keywords/purposes)
"""

if __name__ == "__main__":
    import json
    
    print("Example Positive Pair:")
    print(json.dumps(POSITIVE_PAIRS_EXAMPLE[0], indent=2))
    
    print("\n" + "="*60)
    
    print("\nExample Triplet (list format):")
    print(json.dumps(TRIPLETS_EXAMPLE[0], indent=2))
    
    print(EXPECTED_OUTPUT)
