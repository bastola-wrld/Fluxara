# terraform/main.tf
provider "aws" {
  region = "us-east-1"
}

# VPC for Fluxara Infrastructure
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "fluxara-vpc"
  cidr   = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]
  
  enable_nat_gateway = true
}

# RDS PostGIS Database
resource "aws_db_instance" "fluxara_db" {
  identifier           = "fluxara-prod-db"
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.medium"
  db_name              = "fluxara"
  username             = var.db_username
  password             = var.db_password
  parameter_group_name = "default.postgres15"
  skip_final_snapshot  = true
  
  # Ensure PostGIS is enabled in the DB later
}

# ECS Cluster for Fluxara Engine
resource "aws_ecs_cluster" "fluxara_cluster" {
  name = "fluxara-production"
}

# ECR Repositories
resource "aws_ecr_repository" "api" {
  name = "fluxara-api"
}

resource "aws_ecr_repository" "frontend" {
  name = "fluxara-frontend"
}

# S3 Bucket for Satellite Data (TROPOMI)
resource "aws_s3_bucket" "satellite_data" {
  bucket = "fluxara-satellite-telemetry-prod"
}

variable "db_username" { default = "fluxara_admin" }
variable "db_password" { sensitive = true }
