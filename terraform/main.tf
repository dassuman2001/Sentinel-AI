terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS region for deployment"
}

variable "project_name" {
  type        = string
  default     = "sentinel-ai"
  description = "Project name tag for tagging resources"
}

output "aws_region" {
  value = var.aws_region
}
