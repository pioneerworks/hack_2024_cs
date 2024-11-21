from dotenv import load_dotenv
from typing import List, Dict, Optional
import anthropic
import numpy as np
import os
import tiktoken
import sys
from pathlib import Path

# Get the project root (hack_2024_cs)
current_file = Path(__file__).resolve()
project_root = current_file.parents[1]  # Go up 2 levels from the current file

# Verify we're in the correct directory
if project_root.name != "hack_2024_cs":
    raise RuntimeError("Could not find hack_2024_cs project root")

# Load environment variables from project root
load_dotenv(project_root / ".env")

# Add to Python path if needed
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Now use absolute imports
from llm.lib.vector_store import VectorStore
from llm.lib.embedding import EmbeddingGenerator
from llm.lib.data_preparation import get_project_root

class QAGenerator:
    def __init__(self, max_tokens: int = 4096, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the QA Generator.
        
        Args:
            max_tokens (int): Maximum tokens for context
            model (str): Model to use for generation
        """
        self.max_tokens = max_tokens
        self.model = model
        self.project_root = get_project_root()
        
        # Initialize Anthropic client
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("Anthropic API key not found in environment variables")
        self.client = anthropic.Anthropic()
        
        # Initialize vector store and embedding generator
        self.vector_store = VectorStore()
        self.vector_store.load(f"{self.project_root}/llm/data/vector_store")
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Claude's encoding

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        return len(self.tokenizer.encode(text))

    def get_relevant_chunks(self, question: str, k: int = 5) -> List[Dict]:
        """
        Get relevant text chunks for a question.
        
        Args:
            question (str): User's question
            k (int): Number of chunks to retrieve
            
        Returns:
            List[Dict]: List of relevant chunks with metadata
        """
        # Generate embedding for question
        question_embedding = self.embedding_generator.generate_embeddings([question])[0]
        
        # Search vector store
        distances, indices = self.vector_store.search(
            np.array(question_embedding).reshape(1, -1), 
            k=k
        )
        
        # Get metadata for results
        results = self.vector_store.get_metadata(indices)
        
        # Add distances to results
        for i, result in enumerate(results):
            result['distance'] = float(distances[0][i])
        
        return results

    def construct_prompt(self, question: str, context_chunks: List[Dict]) -> str:
        """
        Construct a prompt from question and context chunks.
        
        Args:
            question (str): User's question
            context_chunks (List[Dict]): Relevant context chunks
            
        Returns:
            str: Constructed prompt
        """
        
        # Add context chunks, keeping track of tokens
        base_prompt = (
            "You are a helpful agent that helps answers questions that homebase customer support agents have while they are working with problems of their customers. "
            "You are given a question and a set of context that contains information about the customer's problem or question. "
            "Only focus on the information within <search_tool_context> to </search_tool_context>, do not invent or create new information. "
            "The context is derived from a set of articles as well as data from internal slack conversations where these questions may have been discussed in the past. "
            "Format your response using proper Markdown syntax:\n"
            "For bullet points, start each item on a new line with '* ' (asterisk followed by a space):\n"
            "Example:\n"
            "* First item\n"
            "* Second item\n\n"
            "For numbered lists:\n"
            "1. First item\n"
            "2. Second item\n\n"
            "You answer should be straight forward and to the point. Don't use words like 'According to the context provided' or 'Based on the context provided' instead just state the answer. "
            "Also avoid using terms like 'articles states' or 'according to the article' instead just use the information given in the context to answer the question. "
            "If the answer cannot be found in the context, say 'I don't have enough information to answer that question.' "
            "Total output characters should be less than 50000. "
            "If you find the answer, include the relevant article URLs at the bottom of your response using the format: "
            "\n\n---\n\nFor more information, see: [Article Title or Slack thread url](URL)\n\n"
        )
        context = ""
        total_tokens = self.count_tokens(base_prompt + question)
        
        for chunk in sorted(context_chunks, key=lambda x: x['distance']):
            chunk_text = f"Article URL: {chunk['url']}\n{chunk['text']}\n\n"
            chunk_tokens = self.count_tokens(chunk_text)
            
            # Check if adding this chunk would exceed token limit
            if total_tokens + chunk_tokens + 100 < self.max_tokens:  # 100 tokens buffer
                context += chunk_text
                total_tokens += chunk_tokens
            else:
                break

        # Construct final prompt
        prompt = f"{base_prompt}<search_tool_context> {context} </search_tool_context>\nQuestion: {question}\nAnswer:"
        return prompt

    def generate_answer(self, question: str) -> str:
        """
        Generate an answer for a question.
        
        Args:
            question (str): User's question
            
        Returns:
            str: Generated answer
        """
        # Get relevant chunks
        context_chunks = self.get_relevant_chunks(question)
        
        # Construct prompt
        prompt = self.construct_prompt(question, context_chunks)
        print("\n\n Prompt:")
        print(prompt)
        print("\n\n")
        try:
            # Generate response using Anthropic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
                temperature=1
            )

            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I apologize, but I encountered an error while generating the answer."

def qa_function(question: str):
    """
    Main function to test the QA generator.
    """
    qa_generator = QAGenerator()
    
    # Test questions
    # test_questions = [
    #     # "What is Task Manager in Homebase?",
    #     "How do I handle payroll corrections after December?",
    #     # "What should I do if I need to change my company's legal address?"
    #     #  "Where are the cx tax returns/payments found"
    #     # "Hi team, I have a customer who's having an issue with their Breaks. They have set up their settings to grant employees to have 10 minute paid breaks. However, on the timesheets, breaks over 10 mins are still being calculated as Paid."
    # ]
    
    print(f"\nQuestion: {question}")
    print("\nAnswer:")
    answer = qa_generator.generate_answer(question)
    print("\n\n")
    print(answer)
    print("\n\n")
    print("-" * 80)
    return answer








