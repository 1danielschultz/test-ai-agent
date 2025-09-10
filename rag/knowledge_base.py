"""
QuickBooks Online RAG Knowledge Base
Handles document processing, embedding generation, and vector search
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import pickle
from pathlib import Path

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    print("Required packages not installed. Run: pip install sentence-transformers faiss-cpu numpy")

@dataclass
class Document:
    """Represents a document in the knowledge base"""
    id: str
    title: str
    content: str
    category: str
    keywords: List[str]
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class QuickBooksRAG:
    """RAG system for QuickBooks Online troubleshooting"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "vector_store"):
        self.model_name = model_name
        self.index_path = index_path
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.Index] = None
        self.model: Optional[SentenceTransformer] = None
        
        # Ensure vector store directory exists
        Path(index_path).mkdir(exist_ok=True)
        
        # Load pre-existing data if available
        self.load_index()
    
    def initialize_model(self):
        """Initialize the sentence transformer model"""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
                print(f"Loaded embedding model: {self.model_name}")
            except Exception as e:
                print(f"Error loading model: {e}")
                raise
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the knowledge base"""
        self.documents.extend(documents)
        
        # Generate embeddings for new documents
        self.initialize_model()
        new_embeddings = self._generate_embeddings([doc.content for doc in documents])
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        # Rebuild FAISS index
        self._build_index()
        self.save_index()
        
        print(f"Added {len(documents)} documents to knowledge base")
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if self.model is None:
            self.initialize_model()
        
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return np.array(embeddings)
    
    def _build_index(self):
        """Build FAISS index from embeddings"""
        if self.embeddings is None or len(self.embeddings) == 0:
            return
        
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
        
        print(f"Built FAISS index with {self.index.ntotal} documents")
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if self.index is None or self.model is None:
            print("Knowledge base not initialized")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= min_score and idx < len(self.documents):
                doc = self.documents[idx]
                results.append({
                    'document': doc,
                    'score': float(score),
                    'relevance': 'high' if score > 0.8 else 'medium' if score > 0.6 else 'low'
                })
        
        return results
    
    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """Get context for RAG prompt"""
        results = self.search(query, top_k=10)
        
        context_parts = []
        current_tokens = 0
        
        for result in results:
            doc = result['document']
            content = f"## {doc.title}\n{doc.content}\n"
            
            # Rough token estimation (4 chars per token)
            estimated_tokens = len(content) // 4
            
            if current_tokens + estimated_tokens > max_tokens:
                break
            
            context_parts.append(content)
            current_tokens += estimated_tokens
        
        return "\n".join(context_parts)
    
    def save_index(self):
        """Save the vector index and documents"""
        if self.index is not None:
            faiss.write_index(self.index, f"{self.index_path}/faiss.index")
        
        # Save documents and embeddings
        with open(f"{self.index_path}/documents.pkl", 'wb') as f:
            pickle.dump(self.documents, f)
        
        if self.embeddings is not None:
            np.save(f"{self.index_path}/embeddings.npy", self.embeddings)
        
        # Save metadata
        metadata = {
            'model_name': self.model_name,
            'num_documents': len(self.documents),
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0
        }
        
        with open(f"{self.index_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_index(self):
        """Load existing vector index and documents"""
        try:
            # Load metadata
            with open(f"{self.index_path}/metadata.json", 'r') as f:
                metadata = json.load(f)
            
            # Load documents
            with open(f"{self.index_path}/documents.pkl", 'rb') as f:
                self.documents = pickle.load(f)
            
            # Load embeddings
            self.embeddings = np.load(f"{self.index_path}/embeddings.npy")
            
            # Load FAISS index
            self.index = faiss.read_index(f"{self.index_path}/faiss.index")
            
            print(f"Loaded knowledge base with {len(self.documents)} documents")
            
        except FileNotFoundError:
            print("No existing knowledge base found. Starting fresh.")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        categories = {}
        for doc in self.documents:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'categories': categories,
            'model_name': self.model_name,
            'index_size': self.index.ntotal if self.index else 0
        }

def create_quickbooks_knowledge_base() -> List[Document]:
    """Create initial QuickBooks Online knowledge base"""
    documents = [
        Document(
            id="qb001",
            title="Connecting Bank Accounts to QuickBooks Online",
            content="""
            To connect your bank account to QuickBooks Online:

            1. Navigate to Banking > Overview in your QuickBooks Online account
            2. Click "Connect account" button
            3. Search for your bank using the search bar
            4. Select your bank from the list
            5. Enter your online banking credentials (username and password)
            6. Choose which accounts you want to connect to QuickBooks
            7. Click "Connect" to establish the connection

            Troubleshooting Connection Issues:
            - Ensure your bank supports QuickBooks integration
            - Verify your online banking credentials are correct
            - Clear browser cache and cookies if connection fails
            - Some banks require additional security steps like two-factor authentication
            - Contact your bank if you're locked out of your online banking

            Supported Banks: Most major banks including Chase, Bank of America, Wells Fargo, Citi, and over 14,000 financial institutions.
            """,
            category="Banking",
            keywords=["bank connection", "banking", "connect account", "financial institution", "credentials"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/bank-feeds/connect-bank-and-credit-card-accounts-to-quickbooks-online/00/203726"
        ),
        
        Document(
            id="qb002",
            title="Resolving Bank Sync Errors",
            content="""
            Common bank sync errors and solutions:

            Error 103 - Invalid Login Credentials:
            - Update your banking credentials in QuickBooks
            - Go to Banking > Overview > Click gear icon next to bank > Update
            - Re-enter your current online banking username and password

            Error 105 - Bank Site Maintenance:
            - Wait for bank maintenance to complete
            - Try reconnecting after a few hours
            - Check your bank's website for maintenance schedules

            Error 185 - Multiple Attempts:
            - You've attempted to connect too many times
            - Wait 24 hours before trying again
            - Contact QuickBooks support if issue persists

            General Sync Issues:
            1. Disconnect and reconnect your bank account
            2. Update your browser to the latest version
            3. Disable browser extensions that might interfere
            4. Clear browser cache and cookies
            5. Try using an incognito/private browsing window

            If problems persist, manually upload bank statements or contact QuickBooks support.
            """,
            category="Banking",
            keywords=["sync error", "bank error", "connection failed", "error 103", "error 105", "error 185"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/bank-feeds/fix-bank-errors-in-quickbooks-online/00/203764"
        ),

        Document(
            id="qb003",
            title="Creating Profit and Loss Reports",
            content="""
            To generate a Profit and Loss (P&L) report in QuickBooks Online:

            Step-by-Step Instructions:
            1. Go to Reports in the left navigation menu
            2. Search for "Profit and Loss" or find it under "Business Overview"
            3. Click on "Profit and Loss" report
            4. Select your desired date range (monthly, quarterly, yearly, or custom)
            5. Click "Display" to generate the report

            Customizing Your P&L Report:
            - Change accounting method (Cash vs Accrual)
            - Add or remove columns
            - Filter by location, class, or customer
            - Compare periods side by side
            - Add subrows for more detail

            Understanding Your P&L:
            - Income section shows all revenue streams
            - Cost of Goods Sold (COGS) shows direct costs
            - Gross Profit = Total Income - COGS
            - Expenses section lists all business expenses
            - Net Income = Gross Profit - Total Expenses

            Exporting and Sharing:
            - Export to Excel, PDF, or print
            - Email directly from QuickBooks
            - Save as a memorized report for regular use
            - Schedule automatic delivery to stakeholders
            """,
            category="Reports",
            keywords=["profit and loss", "P&L", "financial report", "income statement", "revenue", "expenses"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/reports/run-a-profit-and-loss-report/00/203768"
        ),

        Document(
            id="qb004",
            title="QuickBooks Online Payroll Setup",
            content="""
            Setting up payroll in QuickBooks Online:

            Prerequisites:
            - QuickBooks Online Plus or Advanced subscription
            - Payroll add-on subscription
            - Employer Identification Number (EIN)
            - State unemployment account numbers

            Initial Setup Steps:
            1. Go to Payroll > Overview
            2. Click "Get started" if payroll isn't set up
            3. Verify your company information
            4. Set up federal and state tax accounts
            5. Add employee information and pay details

            Adding Employees:
            1. Go to Payroll > Employees
            2. Click "Add an employee"
            3. Enter personal information (name, address, SSN)
            4. Set up pay details (salary/hourly, pay frequency)
            5. Configure tax withholdings (W-4 information)
            6. Add any deductions or benefits

            Running Payroll:
            1. Go to Payroll > Run payroll
            2. Select pay period and employees
            3. Review hours, rates, and deductions
            4. Preview payroll before processing
            5. Submit payroll for processing

            Tax Compliance:
            - QuickBooks automatically calculates taxes
            - Files federal and state tax forms
            - Handles W-2s and 1099s year-end
            - Provides tax penalty protection

            Common Issues:
            - Employee missing from payroll run
            - Incorrect tax calculations
            - Direct deposit setup problems
            - Year-end processing questions
            """,
            category="Payroll",
            keywords=["payroll setup", "employees", "taxes", "direct deposit", "W-2", "wages", "salary"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/payroll/set-up-payroll-in-quickbooks-online/00/203770"
        ),

        Document(
            id="qb005",
            title="Reconciling Bank Accounts",
            content="""
            Monthly bank reconciliation in QuickBooks Online:

            Before You Start:
            - Gather your bank statement
            - Ensure all transactions are entered in QuickBooks
            - Have your previous reconciliation summary available

            Reconciliation Process:
            1. Go to Accounting > Reconcile
            2. Select the bank account to reconcile
            3. Enter statement date and ending balance from bank statement
            4. Match transactions between QuickBooks and bank statement
            5. Check off matching transactions
            6. Add any missing transactions
            7. Resolve any discrepancies

            Common Discrepancies:
            - Timing differences (outstanding checks/deposits)
            - Bank fees not recorded in QuickBooks
            - Interest earned not entered
            - Duplicate transactions
            - Transactions recorded in wrong amounts

            Troubleshooting Tips:
            - Start with the largest discrepancies first
            - Check for transposed numbers
            - Look for missing or duplicate transactions
            - Verify dates are correct
            - Consider bank fees and interest

            When Reconciliation Won't Balance:
            1. Double-check ending balance from statement
            2. Look for outstanding transactions from previous periods
            3. Verify beginning balance matches previous reconciliation
            4. Check for uncleared transactions
            5. Consider making an adjusting entry if difference is minimal

            Benefits of Regular Reconciliation:
            - Catch errors early
            - Detect fraudulent activity
            - Ensure accurate financial reporting
            - Maintain clean books for tax preparation
            """,
            category="Banking",
            keywords=["reconcile", "bank reconciliation", "outstanding checks", "deposits", "balance", "statement"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/bank-feeds/reconcile-an-account-in-quickbooks-online/00/203772"
        ),

        Document(
            id="qb006",
            title="Managing Customers and Invoicing",
            content="""
            Customer management and invoicing in QuickBooks Online:

            Adding Customers:
            1. Go to Sales > Customers
            2. Click "New customer"
            3. Enter customer information (name, address, contact details)
            4. Set payment terms and preferred delivery method
            5. Add any notes or attachments

            Creating Invoices:
            1. Go to Sales > Create invoice
            2. Select customer from dropdown
            3. Add products/services to invoice lines
            4. Set quantities, rates, and descriptions
            5. Apply discounts or add additional charges
            6. Choose invoice template and customize as needed
            7. Preview and send or save

            Invoice Customization:
            - Add your logo and business information
            - Customize colors and fonts
            - Include payment terms and late fees
            - Add custom fields for additional information
            - Set up automatic invoice numbering

            Payment Processing:
            - Enable online payments (credit cards, ACH)
            - Set up QuickBooks Payments account
            - Send payment reminders automatically
            - Track payment status and aging

            Recurring Invoices:
            - Set up for regular customers
            - Choose frequency (weekly, monthly, etc.)
            - Automatically send or save as draft
            - Track recurring invoice performance

            Common Issues:
            - Customer not receiving invoices (check email settings)
            - Payment processing fees
            - Invoice formatting problems
            - Duplicate customer records
            - Incorrect tax calculations
            """,
            category="Sales",
            keywords=["customers", "invoicing", "payments", "sales", "billing", "recurring invoice"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/sales-and-customers/create-invoices-in-quickbooks-online/00/203774"
        ),

        Document(
            id="qb007",
            title="Expense Tracking and Categorization",
            content="""
            Managing expenses in QuickBooks Online:

            Recording Expenses:
            1. Go to Expenses > Create expense
            2. Choose vendor or add new vendor
            3. Select payment method (cash, check, credit card)
            4. Enter expense details and amount
            5. Assign to appropriate expense category
            6. Add receipt photo if available
            7. Save and categorize

            Expense Categories:
            - Set up chart of accounts for your business
            - Use consistent categorization
            - Common categories: Office supplies, Travel, Meals, Insurance
            - Create sub-accounts for detailed tracking
            - Map bank transactions to categories

            Receipt Management:
            - Use QuickBooks mobile app to capture receipts
            - Upload receipts from desktop
            - Forward receipt emails to QuickBooks
            - Store digital copies for record keeping

            Mileage Tracking:
            - Use QuickBooks mobile app for automatic tracking
            - Manually enter trips with start/end locations
            - Set business vs. personal percentages
            - Generate mileage reports for tax deduction

            Credit Card Expenses:
            - Connect credit card accounts to QuickBooks
            - Automatically import transactions
            - Review and categorize imported expenses
            - Match receipts to transactions

            Tax Deductions:
            - Properly categorize deductible expenses
            - Separate business and personal expenses
            - Track receipts for audit purposes
            - Run expense reports by category
            - Consult tax professional for complex situations

            Common Expense Issues:
            - Miscategorized transactions
            - Personal expenses mixed with business
            - Missing receipts
            - Duplicate expense entries
            - Incorrect tax treatment
            """,
            category="Expenses",
            keywords=["expenses", "receipts", "mileage", "deductions", "categories", "vendors", "credit card"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/expenses-and-vendors/enter-and-manage-expenses/00/203776"
        ),

        Document(
            id="qb008",
            title="Inventory Management",
            content="""
            Managing inventory in QuickBooks Online Plus and Advanced:

            Setting Up Inventory:
            1. Go to Sales > Products and Services
            2. Click "New" > "Inventory"
            3. Enter product details (name, SKU, description)
            4. Set initial quantity and cost
            5. Configure reorder points and preferred vendors
            6. Set sales price and income account

            Inventory Tracking:
            - QuickBooks tracks quantity on hand automatically
            - Updates when you create sales or purchase transactions
            - Provides low stock alerts
            - Tracks cost of goods sold (COGS)

            Purchase Orders:
            1. Go to Expenses > Create purchase order
            2. Select vendor
            3. Add inventory items and quantities
            4. Send to vendor
            5. Convert to bill when items received

            Inventory Adjustments:
            - Physical count vs. system count differences
            - Go to Sales > Products and Services > Adjust quantity
            - Enter actual count and reason for adjustment
            - QuickBooks adjusts cost of goods sold

            Inventory Reports:
            - Inventory Valuation Summary
            - Inventory Valuation Detail
            - Physical Inventory Worksheet
            - Stock Status by Item

            Multi-Location Inventory:
            - Available in QuickBooks Advanced
            - Track inventory across multiple locations
            - Transfer between locations
            - Location-specific reporting

            Common Issues:
            - Negative inventory quantities
            - Incorrect cost calculations
            - Items not updating properly
            - Reorder point notifications not working
            - Inventory valuation discrepancies

            Best Practices:
            - Regular physical counts
            - Consistent item naming conventions
            - Proper vendor setup
            - Regular inventory reports review
            - Backup before bulk changes
            """,
            category="Inventory",
            keywords=["inventory", "products", "stock", "purchase orders", "COGS", "valuation", "tracking"],
            source_url="https://quickbooks.intuit.com/learn-support/en-us/inventory/set-up-and-track-your-inventory/00/203778"
        )
    ]
    
    return documents

if __name__ == "__main__":
    # Example usage
    rag = QuickBooksRAG()
    
    # Load initial knowledge base
    documents = create_quickbooks_knowledge_base()
    rag.add_documents(documents)
    
    # Test search functionality
    query = "How do I connect my bank account?"
    results = rag.search(query)
    
    print(f"Search results for: '{query}'")
    for result in results:
        print(f"- {result['document'].title} (Score: {result['score']:.3f})")
    
    # Get context for RAG
    context = rag.get_context(query)
    print(f"\nContext length: {len(context)} characters")
    
    # Show stats
    stats = rag.get_stats()
    print(f"\nKnowledge base stats: {stats}")
