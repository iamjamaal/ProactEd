# Equipment Failure Prediction API Documentation

**Version:** 1.0.0  
**Generated:** 2025-08-01T14:32:54.636573

## Overview

This API provides endpoints for equipment failure prediction and maintenance management.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

All API requests require authentication. Include your API key in the request headers:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### health_check

**Path:** `/health`  
**Methods:** GET

Health check endpoint

```http
GET /health
```

Health check endpoint

---

### predict_failure

**Path:** `/predict`  
**Methods:** POST

Predict equipment failure probability

```http
POST /predict
```

Predict equipment failure probability

---

### batch_predict

**Path:** `/batch_predict`  
**Methods:** POST

Batch prediction for multiple equipment

```http
POST /batch_predict
```

Batch prediction for multiple equipment

---

### get_model_info

**Path:** `/model_info`  
**Methods:** GET

Get model information and performance metrics

```http
GET /model_info
```

Get model information and performance metrics

---

### generate_maintenance_schedule

**Path:** `/maintenance_schedule`  
**Methods:** POST

Generate maintenance schedule for equipment

```http
POST /maintenance_schedule
```

Generate maintenance schedule for equipment

---


## Error Responses

All endpoints return standard HTTP status codes and JSON error responses:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-08-01T14:32:54.642303"
}
```

## Rate Limiting

API requests are limited to 1000 requests per hour per API key.

---

*Generated automatically from source code on 2025-08-01T14:32:54.636573*
