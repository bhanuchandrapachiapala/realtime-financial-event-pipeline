variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  default     = "finpulse"
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API key"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email for anomaly alerts"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  default     = "dev"
}
