---
domain: vertex
difficulty: advanced
tags: vertex, ai, ml, models, aip, llm
---
# Vertex AI & Model Management

## OVERVIEW
Vertex (and the broader AIP platform) represents Palantir's AI/ML infrastructure for building, deploying, and managing machine learning models and AI agents within Foundry.

Key capabilities:
- **Model Training**: Train models on Foundry datasets
- **Model Registry**: Version and track model artifacts
- **Model Deployment**: Serve models via APIs
- **AI Agents**: Build LLM-powered autonomous agents
- **AIP Logic**: Embed AI decisions in Ontology Actions

## PREREQUISITES
Before working with Vertex/AIP:
1. **ML Fundamentals**: Understanding of ML concepts
2. **Python Proficiency**: Advanced Python for model development
3. **Foundry Experience**: Pipeline Builder and Code Repositories
4. **Data Science**: Feature engineering and model evaluation

Recommended prior learning:
- Foundry Platform Essentials (KB-01)
- Pipeline Builder (KB-13)
- Actions & Functions (KB-14)

## CORE_CONTENT

### Model Lifecycle
```
1. Data Preparation (Pipeline Builder)
   └── Feature engineering, train/test split

2. Model Development (Code Repository)
   └── Jupyter notebooks, training scripts

3. Model Training (Compute)
   └── Submit training jobs on Spark

4. Model Evaluation (Metrics)
   └── Accuracy, precision, recall, AUC

5. Model Registration (Registry)
   └── Version, metadata, lineage

6. Model Deployment (Serving)
   └── REST API endpoint

7. Model Monitoring (Operations)
   └── Drift detection, performance
```

### Training Job Configuration
```python
# train_model.py
from foundry_ml import train, register_model
from sklearn.ensemble import RandomForestClassifier

@train(
    input_datasets=["feature_data"],
    output_model="customer_churn_model",
    compute_profile="LARGE"
)
def train_churn_model(feature_data):
    X = feature_data.drop("churned", axis=1)
    y = feature_data["churned"]
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10
    )
    model.fit(X, y)
    
    return model
```

### Model Deployment
```python
# serve_model.py
from foundry_ml import serve

@serve(model_rid="ri.ml.model.xxx")
class ChurnPredictor:
    def predict(self, customer_features: dict) -> float:
        return self.model.predict_proba([customer_features])[0][1]
```

### AIP Integration
```python
# Embedding AI in Ontology Action
from foundry_ml import get_model_client

class PredictChurnAction:
    async def execute(self, ctx):
        customer = await ctx.objects.Customer.get(self.customerId)
        
        # Call deployed model
        model_client = get_model_client("customer_churn_model")
        churn_probability = model_client.predict({
            "tenure": customer.tenure,
            "monthlyCharges": customer.monthlyCharges,
            "totalCharges": customer.totalCharges,
        })
        
        # Update object with prediction
        await customer.update({
            "churnRisk": churn_probability > 0.7 and "HIGH" or "LOW"
        })
```

## EXAMPLES

### End-to-End ML Pipeline
```
1. Data Pipeline
   - Source: CRM transactions
   - Feature engineering: RFM scores
   - Output: feature_dataset

2. Training Job
   - Input: feature_dataset
   - Algorithm: XGBoost
   - Hyperparameter tuning: GridSearch
   - Output: customer_segment_model

3. Deployment
   - Endpoint: /api/v1/segment
   - Input: customer features
   - Output: segment label

4. Integration
   - Ontology Action: SegmentCustomer
   - Calls model endpoint
   - Updates Customer.segment
```

### LLM Agent (AIP)
```python
from aip import Agent, Tool

@Agent(name="CustomerSupport")
class SupportAgent:
    @Tool(description="Get customer details")
    async def get_customer(self, customer_id: str):
        return await self.ctx.objects.Customer.get(customer_id)
    
    @Tool(description="Create support ticket")
    async def create_ticket(self, customer_id: str, issue: str):
        return await self.ctx.actions.CreateTicket.apply({
            "customerId": customer_id,
            "description": issue
        })
```

## COMMON_PITFALLS

1. **Data Leakage**: Features from future data in training
2. **Overfitting**: Model performs poorly on new data
3. **Version Mismatch**: Training vs serving environment differences
4. **Cold Start**: Models need warm-up time
5. **Prompt Injection**: LLM agents need input sanitization

## BEST_PRACTICES

1. **Version Everything**: Data, code, and models
2. **Test Thoroughly**: Unit tests for feature engineering
3. **Monitor Drift**: Track model performance over time
4. **Document Models**: Clear documentation of inputs/outputs
5. **Validate Predictions**: Human review for critical decisions
6. **Secure Endpoints**: API authentication and rate limiting

## REFERENCES
- [Foundry ML Documentation](https://www.palantir.com/docs/foundry/ml/)
- [AIP Documentation](https://www.palantir.com/docs/foundry/aip/)
- [Model Registry Guide](https://www.palantir.com/docs/foundry/models/)
- [AIP Agent Studio](https://www.palantir.com/docs/foundry/aip-agents/)
