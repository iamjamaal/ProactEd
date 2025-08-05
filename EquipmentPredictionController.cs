using Microsoft.AspNetCore.Mvc;
using EquipmentManagement.Services;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;

namespace EquipmentManagement.Controllers
{
    /// <summary>
    /// Controller for equipment failure prediction integration
    /// This shows how to integrate the Python ML service into your .NET application
    /// </summary>
    [ApiController]
    [Route("api/[controller]")]
    public class EquipmentPredictionController : ControllerBase
    {
        private readonly EquipmentPredictionService _predictionService;
        private readonly ILogger<EquipmentPredictionController> _logger;

        public EquipmentPredictionController(
            EquipmentPredictionService predictionService,
            ILogger<EquipmentPredictionController> logger)
        {
            _predictionService = predictionService;
            _logger = logger;
        }

        /// <summary>
        /// Get failure prediction for a single equipment item
        /// </summary>
        /// <param name="equipment">Equipment data</param>
        /// <returns>Prediction result</returns>
        [HttpPost("predict")]
        public async Task<IActionResult> GetEquipmentPrediction([FromBody] EquipmentData equipment)
        {
            try
            {
                _logger.LogInformation($"Requesting prediction for equipment: {equipment.EquipmentId}");
                
                var prediction = await _predictionService.PredictEquipmentFailureAsync(equipment);
                
                if (prediction.Success)
                {
                    // Optional: Save prediction to your database
                    await SavePredictionToDatabase(prediction);
                    
                    _logger.LogInformation($"Prediction successful for equipment {equipment.EquipmentId}: {prediction.RiskLevel} risk");
                    
                    return Ok(new
                    {
                        success = true,
                        prediction = prediction,
                        recommendations = GetMaintenanceRecommendations(prediction)
                    });
                }
                else
                {
                    _logger.LogWarning($"Prediction failed for equipment {equipment.EquipmentId}: {prediction.Error}");
                    return BadRequest(new
                    {
                        success = false,
                        error = prediction.Error
                    });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting prediction for equipment {equipment.EquipmentId}");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Internal server error during prediction",
                    details = ex.Message
                });
            }
        }

        /// <summary>
        /// Get failure predictions for multiple equipment items
        /// </summary>
        /// <param name="equipmentList">List of equipment data</param>
        /// <returns>Batch prediction results</returns>
        [HttpPost("batch-predict")]
        public async Task<IActionResult> GetBatchPredictions([FromBody] List<EquipmentData> equipmentList)
        {
            try
            {
                _logger.LogInformation($"Requesting batch prediction for {equipmentList.Count} equipment items");
                
                var batchResult = await _predictionService.BatchPredictAsync(equipmentList);
                
                if (batchResult.Success)
                {
                    // Optional: Save all predictions to your database
                    await SaveBatchPredictionsToDatabase(batchResult.Predictions);
                    
                    // Generate summary statistics
                    var summary = GeneratePredictionSummary(batchResult);
                    
                    _logger.LogInformation($"Batch prediction completed: {batchResult.TotalProcessed}/{batchResult.TotalRequested} successful");
                    
                    return Ok(new
                    {
                        success = true,
                        results = batchResult,
                        summary = summary,
                        critical_equipment = batchResult.CriticalEquipment,
                        high_risk_equipment = batchResult.HighRiskEquipment
                    });
                }
                else
                {
                    _logger.LogWarning("Batch prediction failed");
                    return BadRequest(new
                    {
                        success = false,
                        error = "Batch prediction failed"
                    });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during batch prediction");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Internal server error during batch prediction",
                    details = ex.Message
                });
            }
        }

        /// <summary>
        /// Check the health status of the prediction service
        /// </summary>
        /// <returns>Service health information</returns>
        [HttpGet("health")]
        public async Task<IActionResult> CheckServiceHealth()
        {
            try
            {
                var healthStatus = await _predictionService.GetHealthStatusAsync();
                
                return Ok(new
                {
                    success = true,
                    health = healthStatus,
                    is_operational = healthStatus.IsHealthy,
                    last_checked = DateTime.Now
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error checking service health");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Unable to check service health",
                    details = ex.Message
                });
            }
        }

        /// <summary>
        /// Test connection to the prediction service
        /// </summary>
        /// <returns>Connection test results</returns>
        [HttpGet("test-connection")]
        public async Task<IActionResult> TestConnection()
        {
            try
            {
                var testResult = await _predictionService.TestConnectionAsync();
                
                return Ok(new
                {
                    success = testResult.IsConnected,
                    connection_test = testResult
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error testing connection");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Connection test failed",
                    details = ex.Message
                });
            }
        }

        /// <summary>
        /// Get model information and capabilities
        /// </summary>
        /// <returns>Model information</returns>
        [HttpGet("model-info")]
        public async Task<IActionResult> GetModelInfo()
        {
            try
            {
                var modelInfo = await _predictionService.GetModelInfoAsync();
                
                return Ok(new
                {
                    success = true,
                    model_info = modelInfo
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting model info");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Unable to get model information",
                    details = ex.Message
                });
            }
        }

        /// <summary>
        /// Get equipment at risk - returns equipment that needs attention
        /// </summary>
        /// <param name="equipmentList">List of equipment to check</param>
        /// <returns>Equipment at risk</returns>
        [HttpPost("at-risk")]
        public async Task<IActionResult> GetEquipmentAtRisk([FromBody] List<EquipmentData> equipmentList)
        {
            try
            {
                var batchResult = await _predictionService.BatchPredictAsync(equipmentList);
                
                if (batchResult.Success)
                {
                    var atRiskEquipment = batchResult.Predictions
                        .Where(p => p.FailureProbability >= 0.4) // High or Critical risk
                        .OrderByDescending(p => p.FailureProbability)
                        .ToList();
                    
                    return Ok(new
                    {
                        success = true,
                        total_checked = batchResult.TotalProcessed,
                        at_risk_count = atRiskEquipment.Count,
                        at_risk_equipment = atRiskEquipment.Select(p => new
                        {
                            equipment_id = p.EquipmentId,
                            failure_probability = p.FailureProbability,
                            risk_level = p.RiskLevel,
                            priority = GetMaintenancePriority(p),
                            recommended_action = GetRecommendedAction(p)
                        })
                    });
                }
                else
                {
                    return BadRequest(new { success = false, error = "Failed to check equipment risk" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error checking equipment at risk");
                return StatusCode(500, new
                {
                    success = false,
                    error = "Error checking equipment risk",
                    details = ex.Message
                });
            }
        }

        #region Private Helper Methods

        private async Task SavePredictionToDatabase(PredictionResult prediction)
        {
            // TODO: Implement database saving logic
            // Example:
            // var entity = new EquipmentPredictionEntity
            // {
            //     EquipmentId = prediction.EquipmentId,
            //     FailureProbability = prediction.FailureProbability,
            //     RiskLevel = prediction.RiskLevel,
            //     PredictionTimestamp = prediction.PredictionTimestamp,
            //     ModelVersion = prediction.ModelVersion,
            //     ConfidenceScore = prediction.ConfidenceScore
            // };
            // await _dbContext.EquipmentPredictions.AddAsync(entity);
            // await _dbContext.SaveChangesAsync();
            
            _logger.LogInformation($"Prediction saved for equipment {prediction.EquipmentId}");
        }

        private async Task SaveBatchPredictionsToDatabase(List<PredictionResult> predictions)
        {
            // TODO: Implement batch database saving logic
            foreach (var prediction in predictions)
            {
                await SavePredictionToDatabase(prediction);
            }
        }

        private object GeneratePredictionSummary(BatchPredictionResult batchResult)
        {
            var predictions = batchResult.Predictions;
            
            return new
            {
                total_equipment = batchResult.TotalProcessed,
                success_rate = batchResult.SuccessRate,
                risk_distribution = new
                {
                    critical = predictions.Count(p => p.RiskLevel == "Critical"),
                    high = predictions.Count(p => p.RiskLevel == "High"),
                    medium = predictions.Count(p => p.RiskLevel == "Medium"),
                    low = predictions.Count(p => p.RiskLevel == "Low")
                },
                average_failure_probability = predictions.Any() ? predictions.Average(p => p.FailureProbability) : 0,
                equipment_needing_attention = predictions.Count(p => p.FailureProbability >= 0.4),
                highest_risk_equipment = predictions
                    .OrderByDescending(p => p.FailureProbability)
                    .Take(5)
                    .Select(p => new { p.EquipmentId, p.FailureProbability, p.RiskLevel })
            };
        }

        private List<string> GetMaintenanceRecommendations(PredictionResult prediction)
        {
            var recommendations = new List<string>();

            switch (prediction.RiskLevel)
            {
                case "Critical":
                    recommendations.Add("IMMEDIATE ACTION REQUIRED - Schedule emergency maintenance");
                    recommendations.Add("Consider taking equipment offline until maintenance is completed");
                    recommendations.Add("Prepare replacement parts");
                    break;
                case "High":
                    recommendations.Add("Schedule maintenance within 24-48 hours");
                    recommendations.Add("Increase monitoring frequency");
                    recommendations.Add("Have backup equipment ready");
                    break;
                case "Medium":
                    recommendations.Add("Schedule preventive maintenance within the next week");
                    recommendations.Add("Monitor equipment performance closely");
                    break;
                case "Low":
                    recommendations.Add("Continue regular maintenance schedule");
                    recommendations.Add("Monitor during routine inspections");
                    break;
            }

            return recommendations;
        }

        private int GetMaintenancePriority(PredictionResult prediction)
        {
            return prediction.RiskLevel switch
            {
                "Critical" => 1,
                "High" => 2,
                "Medium" => 3,
                "Low" => 4,
                _ => 5
            };
        }

        private string GetRecommendedAction(PredictionResult prediction)
        {
            return prediction.RiskLevel switch
            {
                "Critical" => "Emergency Maintenance Required",
                "High" => "Schedule Urgent Maintenance",
                "Medium" => "Plan Preventive Maintenance",
                "Low" => "Continue Regular Schedule",
                _ => "Monitor"
            };
        }

        #endregion
    }
}
