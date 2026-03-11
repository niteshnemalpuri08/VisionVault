import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Global variable to hold the trained model
model = None

def train_model():
    """
    Generates synthetic data and trains a Linear Regression model.
    Logic: Final Score = (Avg Marks * 0.7) + (Attendance * 0.3) + Noise
    """
    global model
    print("🧠 Training ML Model on Synthetic Data...")

    # 1. Generate 500 random students for training
    np.random.seed(42)
    n_samples = 500

    # Random Marks (40-100)
    math = np.random.randint(40, 100, n_samples)
    phy = np.random.randint(40, 100, n_samples)
    chem = np.random.randint(40, 100, n_samples)
    cs = np.random.randint(40, 100, n_samples)
    eng = np.random.randint(40, 100, n_samples)
    pe = np.random.randint(40, 100, n_samples)
    
    # Random Attendance (50-100)
    attendance = np.random.randint(50, 100, n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        'math': math, 'phy': phy, 'chem': chem, 
        'cs': cs, 'eng': eng, 'pe': pe, 
        'attendance': attendance
    })

    # Define Target: Weighted Formula + Random Noise
    avg_academic = (df['math'] + df['phy'] + df['chem'] + df['cs'] + df['eng'] + df['pe']) / 6
    
    df['final_score'] = (avg_academic * 0.7) + (df['attendance'] * 0.3) + np.random.normal(0, 2, n_samples)

    # Features (X) and Target (y)
    X = df[['math', 'phy', 'chem', 'cs', 'eng', 'pe', 'attendance']]
    y = df['final_score']

    # 2. Train Model
    model = LinearRegression()
    model.fit(X, y)
    print("✅ ML Model Trained Successfully.")

def predict_score(math, phy, chem, cs, eng, pe, attendance):
    """
    Takes a student's current stats and predicts Final Semester Score.
    """
    if model is None:
        train_model()
    
    # Create input array
    input_data = pd.DataFrame([[math, phy, chem, cs, eng, pe, attendance]], 
                              columns=['math', 'phy', 'chem', 'cs', 'eng', 'pe', 'attendance'])
    
    # Predict
    prediction = model.predict(input_data)[0]
    
    # Cap result between 0 and 100
    return round(max(0, min(100, prediction)), 2)

# Auto-train when imported
if __name__ != '__main__':
    train_model()