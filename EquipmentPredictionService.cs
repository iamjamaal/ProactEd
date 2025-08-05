using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace EquipmentManagement.Services
{
    /// <summary>
    /// Service for integrating with Python ML Equipment Failure Prediction API
    /// </summary>
    public class EquipmentPredictionService : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _apiBaseUrl;
        private bool _disposed = false;

        public EquipmentPredictionService(string apiBaseUrl = "http://localhost:5000")
        {
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
            _apiBaseUrl = apiBaseUrl.TrimEnd('/');
        }

        /// <summary>
        /// Predict failure probability for a single equipment item
        /// </summary>
        /// <param name="equipment">Equipment data for prediction</param>
        /// <returns>Prediction result</returns>
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
                    var errorContent = await response.Content.ReadAsStringAsync();
                    throw new Exception($"API call failed: {response.StatusCode} - {errorContent}");
                }
            }
            catch (HttpRequestException ex)
            {
                throw new Exception($"Network error connecting to prediction service: {ex.Message}");
            }
            catch (TaskCanceledException ex)
            {
                throw new Exception($"Prediction request timed out: {ex.Message}");
            }
            catch (Exception ex)
            {
                throw new Exception($"Prediction service error: {ex.Message}");
            }
        }

        /// <summary>
        /// Predict failure probability for multiple equipment items
        /// </summary>
        /// <param name="equipmentList">List of equipment data for batch prediction</param>
        /// <returns>Batch prediction result</returns>
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
                    var errorContent = await response.Content.ReadAsStringAsync();
                    throw new Exception($"Batch prediction failed: {response.StatusCode} - {errorContent}");
                }
            }
            catch (HttpRequestException ex)
            {
                throw new Exception($"Network error during batch prediction: {ex.Message}");
            }
            catch (TaskCanceledException ex)
            {
                throw new Exception($"Batch prediction request timed out: {ex.Message}");
            }
            catch (Exception ex)
            {
                throw new Exception($"Batch prediction error: {ex.Message}");
            }
        }

        /// <summary>
        /// Check if the prediction service is healthy and available
        /// </summary>
        /// <returns>True if service is healthy, false otherwise</returns>
        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_apiBaseUrl}/api/health");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var health = JsonConvert.DeserializeObject<HealthStatus>(content);
                    return health.Status == "healthy" && health.ModelLoaded;
                }
                return false;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Get detailed health status of the prediction service
        /// </summary>
        /// <returns>Health status information</returns>
        public async Task<HealthStatus> GetHealthStatusAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_apiBaseUrl}/api/health");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    return JsonConvert.DeserializeObject<HealthStatus>(content);
                }
                else
                {
                    return new HealthStatus
                    {
                        Status = "unhealthy",
                        ModelLoaded = false,
                        Timestamp = DateTime.Now,
                        Version = "unknown"
                    };
                }
            }
            catch (Exception ex)
            {
                return new HealthStatus
                {
                    Status = "error",
                    ModelLoaded = false,
                    Timestamp = DateTime.Now,
                    Version = "unknown",
                    Error = ex.Message
                };
            }
        }

        /// <summary>
        /// Get model information and capabilities
        /// </summary>
        /// <returns>Model information</returns>
        public async Task<ModelInfo> GetModelInfoAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_apiBaseUrl}/api/model/info");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    return JsonConvert.DeserializeObject<ModelInfo>(content);
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    throw new Exception($"Failed to get model info: {response.StatusCode} - {errorContent}");
                }
            }
            catch (HttpRequestException ex)
            {
                throw new Exception($"Network error getting model info: {ex.Message}");
            }
            catch (Exception ex)
            {
                throw new Exception($"Error getting model info: {ex.Message}");
            }
        }

        /// <summary>
        /// Test the connection to the prediction service
        /// </summary>
        /// <returns>Connection test result</returns>
        public async Task<ConnectionTestResult> TestConnectionAsync()
        {
            var result = new ConnectionTestResult
            {
                TestTimestamp = DateTime.Now
            };

            try
            {
                var healthStatus = await GetHealthStatusAsync();
                result.IsConnected = healthStatus.Status == "healthy";
                result.ServiceStatus = healthStatus.Status;
                result.ModelLoaded = healthStatus.ModelLoaded;
                result.ServiceVersion = healthStatus.Version;
                
                if (result.IsConnected)
                {
                    result.Message = "Connection successful - Service is healthy";
                }
                else
                {
                    result.Message = $"Service is not healthy: {healthStatus.Status}";
                }
            }
            catch (Exception ex)
            {
                result.IsConnected = false;
                result.Message = $"Connection failed: {ex.Message}";
                result.Error = ex.Message;
            }

            return result;
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed && disposing)
            {
                _httpClient?.Dispose();
                _disposed = true;
            }
        }
    }

    // Data Transfer Objects (DTOs) for API communication
    
    /// <summary>
    /// Equipment data for prediction requests
    /// </summary>
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
        public double HumidityLevel { get; set; } = 0.0;
        
        [JsonProperty("dust_accumulation")]
        public double DustAccumulation { get; set; } = 0.0;
        
        [JsonProperty("performance_score")]
        public double PerformanceScore { get; set; } = 0.0;
        
        [JsonProperty("daily_usage_hours")]
        public double DailyUsageHours { get; set; } = 0.0;
    }

    /// <summary>
    /// Prediction result from the ML service
    /// </summary>
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
        
        [JsonProperty("model_version")]
        public string ModelVersion { get; set; }
        
        [JsonProperty("error")]
        public string Error { get; set; }

        // Helper properties for easier integration
        public bool IsCriticalRisk => RiskLevel == "Critical";
        public bool IsHighRisk => RiskLevel == "High" || RiskLevel == "Critical";
        public bool RequiresImmediateAttention => FailureProbability >= 0.7;
        public string RiskColor => RiskLevel switch
        {
            "Critical" => "#dc3545", // Red
            "High" => "#fd7e14",     // Orange
            "Medium" => "#ffc107",   // Yellow
            "Low" => "#28a745",      // Green
            _ => "#6c757d"           // Gray
        };
    }

    /// <summary>
    /// Batch prediction result
    /// </summary>
    public class BatchPredictionResult
    {
        [JsonProperty("success")]
        public bool Success { get; set; }
        
        [JsonProperty("predictions")]
        public List<PredictionResult> Predictions { get; set; } = new List<PredictionResult>();
        
        [JsonProperty("total_requested")]
        public int TotalRequested { get; set; }
        
        [JsonProperty("total_processed")]
        public int TotalProcessed { get; set; }
        
        [JsonProperty("total_errors")]
        public int TotalErrors { get; set; }
        
        [JsonProperty("batch_timestamp")]
        public DateTime BatchTimestamp { get; set; }
        
        [JsonProperty("errors")]
        public List<BatchError> Errors { get; set; } = new List<BatchError>();

        // Helper properties
        public double SuccessRate => TotalRequested > 0 ? (double)TotalProcessed / TotalRequested * 100 : 0;
        public bool HasErrors => TotalErrors > 0;
        public List<PredictionResult> CriticalEquipment => 
            Predictions?.Where(p => p.RiskLevel == "Critical").ToList() ?? new List<PredictionResult>();
        public List<PredictionResult> HighRiskEquipment => 
            Predictions?.Where(p => p.RiskLevel == "High" || p.RiskLevel == "Critical").ToList() ?? new List<PredictionResult>();
    }

    /// <summary>
    /// Batch processing error details
    /// </summary>
    public class BatchError
    {
        [JsonProperty("index")]
        public int Index { get; set; }
        
        [JsonProperty("equipment_id")]
        public string EquipmentId { get; set; }
        
        [JsonProperty("error")]
        public string Error { get; set; }
    }

    /// <summary>
    /// Service health status
    /// </summary>
    public class HealthStatus
    {
        [JsonProperty("status")]
        public string Status { get; set; }
        
        [JsonProperty("timestamp")]
        public DateTime Timestamp { get; set; }
        
        [JsonProperty("version")]
        public string Version { get; set; }
        
        [JsonProperty("model_loaded")]
        public bool ModelLoaded { get; set; }
        
        [JsonProperty("model_info")]
        public Dictionary<string, object> ModelInfo { get; set; }
        
        public string Error { get; set; }
        
        public bool IsHealthy => Status == "healthy" && ModelLoaded;
    }

    /// <summary>
    /// Model information and capabilities
    /// </summary>
    public class ModelInfo
    {
        [JsonProperty("success")]
        public bool Success { get; set; }
        
        [JsonProperty("model_name")]
        public string ModelName { get; set; }
        
        [JsonProperty("model_type")]
        public string ModelType { get; set; }
        
        [JsonProperty("features")]
        public List<string> Features { get; set; } = new List<string>();
        
        [JsonProperty("feature_count")]
        public int FeatureCount { get; set; }
        
        [JsonProperty("required_fields")]
        public List<string> RequiredFields { get; set; } = new List<string>();
        
        [JsonProperty("optional_fields")]
        public List<string> OptionalFields { get; set; } = new List<string>();
        
        [JsonProperty("risk_levels")]
        public List<string> RiskLevels { get; set; } = new List<string>();
        
        [JsonProperty("api_version")]
        public string ApiVersion { get; set; }
        
        [JsonProperty("error")]
        public string Error { get; set; }
    }

    /// <summary>
    /// Connection test result
    /// </summary>
    public class ConnectionTestResult
    {
        public bool IsConnected { get; set; }
        public string Message { get; set; }
        public string ServiceStatus { get; set; }
        public bool ModelLoaded { get; set; }
        public string ServiceVersion { get; set; }
        public DateTime TestTimestamp { get; set; }
        public string Error { get; set; }
    }
}
