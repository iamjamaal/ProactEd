# 🔗 .NET Integration Guide for Equipment Failure Prediction System

## 📋 **Integration Overview**

This guide provides multiple approaches to integrate the Python-based Equipment Failure Prediction System with a .NET Equipment Management Application.

---

## 🚀 **Option 1: REST API Integration (Recommended)**

### **Architecture:**
```
.NET Application → HTTP REST Calls → Python Flask API → ML Model → Response
```

### **Implementation Steps:**

#### **1.1 Enhance Python API for .NET Integration**

**Add CORS support and additional endpoints:**

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for .NET integration

# Enhanced API endpoints for .NET integration
@app.route('/api/equipment/predict', methods=['POST'])
def predict_equipment_failure():
    """
    Enhanced prediction endpoint for .NET integration
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['equipment_id', 'age_months', 'operating_temperature', 
                          'vibration_level', 'power_consumption']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Load model and make prediction
        with open('complete_equipment_failure_prediction_system.pkl', 'rb') as f:
            model_system = pickle.load(f)
        
        model = model_system['model_info']['model_object']
        features = model_system['model_info']['features']
        
        # Prepare input data
        input_data = pd.DataFrame([data])
        for feature in features:
            if feature not in input_data.columns:
                input_data[feature] = 0
        
        X = input_data[features].fillna(0)
        prediction = model.predict(X)[0]
        
        # Calculate risk level
        risk_level = (
            'Critical' if prediction >= 0.7 else
            'High' if prediction >= 0.4 else
            'Medium' if prediction >= 0.2 else
            'Low'
        )
        
        return jsonify({
            'success': True,
            'equipment_id': data['equipment_id'],
            'failure_probability': float(prediction),
            'risk_level': risk_level,
            'prediction_timestamp': datetime.now().isoformat(),
            'model_version': model_system['model_info'].get('model_name', 'Random Forest (Retrained)'),
            'confidence_score': float(1 - abs(prediction - 0.5) * 2)  # Confidence metric
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/equipment/batch-predict', methods=['POST'])
def batch_predict_equipment():
    """
    Batch prediction for multiple equipment items
    """
    try:
        data = request.get_json()
        equipment_list = data.get('equipment_list', [])
        
        if not equipment_list:
            return jsonify({
                'success': False,
                'error': 'No equipment data provided'
            }), 400
        
        results = []
        for equipment in equipment_list:
            # Use single prediction logic for each item
            # Implementation similar to above
            pass
        
        return jsonify({
            'success': True,
            'predictions': results,
            'total_processed': len(equipment_list),
            'batch_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for .NET monitoring
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'model_loaded': True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### **1.2 .NET Integration Code**

**Create a service class for API integration:**

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class EquipmentPredictionService
{
    private readonly HttpClient _httpClient;
    private readonly string _apiBaseUrl;

    public EquipmentPredictionService(string apiBaseUrl = "http://localhost:5000")
    {
        _httpClient = new HttpClient();
        _apiBaseUrl = apiBaseUrl;
    }

    public async Task<PredictionResult> PredictEquipmentFailureAsync(EquipmentData equipment)
    {
        try
        {
            var json = JsonConvert.SerializeObject(equipment);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_apiBaseUrl}/api/equipment/predict", content);
            
            if (response.IsSuccessStatusCode)
            {
                var responseContent = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<PredictionResult>(responseContent);
            }
            else
            {
                throw new Exception($"API call failed: {response.StatusCode}");
            }
        }
        catch (Exception ex)
        {
            throw new Exception($"Prediction service error: {ex.Message}");
        }
    }

    public async Task<BatchPredictionResult> BatchPredictAsync(List<EquipmentData> equipmentList)
    {
        try
        {
            var requestData = new { equipment_list = equipmentList };
            var json = JsonConvert.SerializeObject(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_apiBaseUrl}/api/equipment/batch-predict", content);
            
            if (response.IsSuccessStatusCode)
            {
                var responseContent = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<BatchPredictionResult>(responseContent);
            }
            else
            {
                throw new Exception($"Batch prediction failed: {response.StatusCode}");
            }
        }
        catch (Exception ex)
        {
            throw new Exception($"Batch prediction error: {ex.Message}");
        }
    }

    public async Task<bool> IsServiceHealthyAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_apiBaseUrl}/api/health");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }
}

// Data models for .NET integration
public class EquipmentData
{
    [JsonProperty("equipment_id")]
    public string EquipmentId { get; set; }
    
    [JsonProperty("age_months")]
    public int AgeMonths { get; set; }
    
    [JsonProperty("operating_temperature")]
    public double OperatingTemperature { get; set; }
    
    [JsonProperty("vibration_level")]
    public double VibrationLevel { get; set; }
    
    [JsonProperty("power_consumption")]
    public double PowerConsumption { get; set; }
    
    [JsonProperty("humidity_level")]
    public double HumidityLevel { get; set; }
    
    [JsonProperty("dust_accumulation")]
    public double DustAccumulation { get; set; }
    
    [JsonProperty("performance_score")]
    public double PerformanceScore { get; set; }
    
    [JsonProperty("daily_usage_hours")]
    public double DailyUsageHours { get; set; }
}

public class PredictionResult
{
    [JsonProperty("success")]
    public bool Success { get; set; }
    
    [JsonProperty("equipment_id")]
    public string EquipmentId { get; set; }
    
    [JsonProperty("failure_probability")]
    public double FailureProbability { get; set; }
    
    [JsonProperty("risk_level")]
    public string RiskLevel { get; set; }
    
    [JsonProperty("prediction_timestamp")]
    public DateTime PredictionTimestamp { get; set; }
    
    [JsonProperty("confidence_score")]
    public double ConfidenceScore { get; set; }
    
    [JsonProperty("error")]
    public string Error { get; set; }
}

public class BatchPredictionResult
{
    [JsonProperty("success")]
    public bool Success { get; set; }
    
    [JsonProperty("predictions")]
    public List<PredictionResult> Predictions { get; set; }
    
    [JsonProperty("total_processed")]
    public int TotalProcessed { get; set; }
    
    [JsonProperty("batch_timestamp")]
    public DateTime BatchTimestamp { get; set; }
}
```

#### **1.3 Usage in .NET Application**

```csharp
public class EquipmentController : Controller
{
    private readonly EquipmentPredictionService _predictionService;

    public EquipmentController()
    {
        _predictionService = new EquipmentPredictionService("http://localhost:5000");
    }

    [HttpPost]
    public async Task<IActionResult> GetEquipmentPrediction([FromBody] EquipmentData equipment)
    {
        try
        {
            var prediction = await _predictionService.PredictEquipmentFailureAsync(equipment);
            
            if (prediction.Success)
            {
                // Update your .NET database with prediction results
                await UpdateEquipmentRiskLevel(equipment.EquipmentId, prediction);
                
                return Json(new 
                {
                    success = true,
                    prediction = prediction
                });
            }
            else
            {
                return Json(new 
                {
                    success = false,
                    error = prediction.Error
                });
            }
        }
        catch (Exception ex)
        {
            return Json(new 
            {
                success = false,
                error = ex.Message
            });
        }
    }

    private async Task UpdateEquipmentRiskLevel(string equipmentId, PredictionResult prediction)
    {
        // Update your .NET database with the prediction results
        // This integrates the ML predictions with your existing equipment management system
    }
}
```

---

## 🔗 **Option 2: Database Integration**

### **Architecture:**
```
Python System → Shared Database ← .NET Application
```

#### **2.1 Shared Database Schema**

```sql
-- Create prediction results table
CREATE TABLE EquipmentPredictions (
    Id INT PRIMARY KEY IDENTITY(1,1),
    EquipmentId NVARCHAR(50) NOT NULL,
    FailureProbability DECIMAL(5,4) NOT NULL,
    RiskLevel NVARCHAR(20) NOT NULL,
    PredictionTimestamp DATETIME2 NOT NULL,
    ModelVersion NVARCHAR(50),
    ConfidenceScore DECIMAL(5,4),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- Create equipment features table for ML input
CREATE TABLE EquipmentFeatures (
    Id INT PRIMARY KEY IDENTITY(1,1),
    EquipmentId NVARCHAR(50) NOT NULL,
    AgeMonths INT,
    OperatingTemperature DECIMAL(8,2),
    VibrationLevel DECIMAL(8,2),
    PowerConsumption DECIMAL(8,2),
    HumidityLevel DECIMAL(5,4),
    DustAccumulation DECIMAL(5,4),
    PerformanceScore DECIMAL(5,4),
    DailyUsageHours DECIMAL(5,2),
    LastUpdated DATETIME2 DEFAULT GETDATE()
);
```

#### **2.2 Python Database Integration**

```python
import pyodbc
import pandas as pd
from datetime import datetime

class DatabaseIntegration:
    def __init__(self, connection_string):
        self.connection_string = connection_string
    
    def get_equipment_features(self, equipment_id=None):
        """Get equipment features from shared database"""
        with pyodbc.connect(self.connection_string) as conn:
            query = """
                SELECT EquipmentId, AgeMonths, OperatingTemperature, VibrationLevel,
                       PowerConsumption, HumidityLevel, DustAccumulation, 
                       PerformanceScore, DailyUsageHours
                FROM EquipmentFeatures
            """
            if equipment_id:
                query += " WHERE EquipmentId = ?"
                return pd.read_sql(query, conn, params=[equipment_id])
            else:
                return pd.read_sql(query, conn)
    
    def save_predictions(self, predictions):
        """Save prediction results to shared database"""
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            
            for pred in predictions:
                cursor.execute("""
                    INSERT INTO EquipmentPredictions 
                    (EquipmentId, FailureProbability, RiskLevel, PredictionTimestamp, ModelVersion, ConfidenceScore)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, pred['equipment_id'], pred['failure_probability'], pred['risk_level'],
                    pred['timestamp'], pred['model_version'], pred['confidence_score'])
            
            conn.commit()

# Scheduled prediction job
def run_scheduled_predictions():
    """Run predictions for all equipment and save to database"""
    db = DatabaseIntegration("your_connection_string")
    
    # Get all equipment features
    equipment_data = db.get_equipment_features()
    
    # Run predictions
    predictions = []
    for _, row in equipment_data.iterrows():
        prediction = predict_single_equipment(row)
        predictions.append(prediction)
    
    # Save results
    db.save_predictions(predictions)
```

#### **2.3 .NET Database Access**

```csharp
public class PredictionRepository
{
    private readonly string _connectionString;

    public PredictionRepository(string connectionString)
    {
        _connectionString = connectionString;
    }

    public async Task<List<EquipmentPrediction>> GetEquipmentPredictionsAsync(string equipmentId = null)
    {
        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();

        var query = @"
            SELECT EquipmentId, FailureProbability, RiskLevel, PredictionTimestamp, 
                   ModelVersion, ConfidenceScore, CreatedAt
            FROM EquipmentPredictions";

        if (!string.IsNullOrEmpty(equipmentId))
            query += " WHERE EquipmentId = @EquipmentId";

        query += " ORDER BY PredictionTimestamp DESC";

        using var command = new SqlCommand(query, connection);
        if (!string.IsNullOrEmpty(equipmentId))
            command.Parameters.AddWithValue("@EquipmentId", equipmentId);

        var predictions = new List<EquipmentPrediction>();
        using var reader = await command.ExecuteReaderAsync();

        while (await reader.ReadAsync())
        {
            predictions.Add(new EquipmentPrediction
            {
                EquipmentId = reader["EquipmentId"].ToString(),
                FailureProbability = Convert.ToDouble(reader["FailureProbability"]),
                RiskLevel = reader["RiskLevel"].ToString(),
                PredictionTimestamp = Convert.ToDateTime(reader["PredictionTimestamp"]),
                ModelVersion = reader["ModelVersion"].ToString(),
                ConfidenceScore = Convert.ToDouble(reader["ConfidenceScore"]),
                CreatedAt = Convert.ToDateTime(reader["CreatedAt"])
            });
        }

        return predictions;
    }

    public async Task UpdateEquipmentFeaturesAsync(EquipmentFeatures features)
    {
        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();

        var query = @"
            MERGE EquipmentFeatures AS target
            USING (SELECT @EquipmentId as EquipmentId) AS source
            ON target.EquipmentId = source.EquipmentId
            WHEN MATCHED THEN
                UPDATE SET AgeMonths = @AgeMonths, 
                          OperatingTemperature = @OperatingTemperature,
                          VibrationLevel = @VibrationLevel,
                          PowerConsumption = @PowerConsumption,
                          HumidityLevel = @HumidityLevel,
                          DustAccumulation = @DustAccumulation,
                          PerformanceScore = @PerformanceScore,
                          DailyUsageHours = @DailyUsageHours,
                          LastUpdated = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (EquipmentId, AgeMonths, OperatingTemperature, VibrationLevel,
                       PowerConsumption, HumidityLevel, DustAccumulation, 
                       PerformanceScore, DailyUsageHours)
                VALUES (@EquipmentId, @AgeMonths, @OperatingTemperature, @VibrationLevel,
                       @PowerConsumption, @HumidityLevel, @DustAccumulation, 
                       @PerformanceScore, @DailyUsageHours);";

        using var command = new SqlCommand(query, connection);
        command.Parameters.AddWithValue("@EquipmentId", features.EquipmentId);
        command.Parameters.AddWithValue("@AgeMonths", features.AgeMonths);
        command.Parameters.AddWithValue("@OperatingTemperature", features.OperatingTemperature);
        command.Parameters.AddWithValue("@VibrationLevel", features.VibrationLevel);
        command.Parameters.AddWithValue("@PowerConsumption", features.PowerConsumption);
        command.Parameters.AddWithValue("@HumidityLevel", features.HumidityLevel);
        command.Parameters.AddWithValue("@DustAccumulation", features.DustAccumulation);
        command.Parameters.AddWithValue("@PerformanceScore", features.PerformanceScore);
        command.Parameters.AddWithValue("@DailyUsageHours", features.DailyUsageHours);

        await command.ExecuteNonQueryAsync();
    }
}
```

---

## 🐳 **Option 3: Docker Container Integration**

### **3.1 Containerize Python Service**

```dockerfile
# Dockerfile for Python prediction service
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "equipment_api.py"]
```

### **3.2 Docker Compose with .NET**

```yaml
version: '3.8'

services:
  prediction-service:
    build: ./python-ml-service
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./models:/app/models
    restart: unless-stopped

  dotnet-app:
    build: ./dotnet-equipment-app
    ports:
      - "8080:80"
    depends_on:
      - prediction-service
      - database
    environment:
      - PREDICTION_SERVICE_URL=http://prediction-service:5000
      - ConnectionStrings__DefaultConnection=Server=database;Database=EquipmentDB;User=sa;Password=YourPassword;

  database:
    image: mcr.microsoft.com/mssql/server:2019-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourPassword
      - MSSQL_DB=EquipmentDB
    ports:
      - "1433:1433"
    volumes:
      - db_data:/var/opt/mssql

volumes:
  db_data:
```

---

## 📋 **Implementation Recommendations**

### **Recommended Approach: REST API Integration**

**Why this is best:**
1. **Loose Coupling**: Services remain independent
2. **Scalability**: Can scale Python service separately
3. **Technology Agnostic**: Easy to maintain and update
4. **Testability**: Services can be tested independently
5. **Deployment Flexibility**: Can deploy on different servers

### **Implementation Timeline:**

#### **Week 1: API Enhancement**
- Enhance Python Flask API with .NET-friendly endpoints
- Add CORS support and error handling
- Create comprehensive API documentation

#### **Week 2: .NET Integration**
- Create .NET service classes for API integration
- Implement data models and serialization
- Add error handling and logging

#### **Week 3: Testing & Validation**
- Unit tests for both Python and .NET components
- Integration testing between systems
- Performance testing under load

#### **Week 4: Deployment & Documentation**
- Deploy Python service (Docker recommended)
- Update .NET application with prediction features
- Create deployment and maintenance guides

---

## 🛠️ **Next Steps**

1. **Choose Integration Method**: REST API recommended
2. **Set up Development Environment**: Docker for consistency
3. **Enhance Python API**: Add .NET-specific endpoints
4. **Create .NET Service Layer**: Implement HTTP client
5. **Test Integration**: Comprehensive testing strategy
6. **Deploy and Monitor**: Production deployment with monitoring

Would you like me to help implement any specific part of this integration?
