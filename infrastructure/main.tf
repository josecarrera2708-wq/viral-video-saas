terraform {
  required_version = ">= 1.0"
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

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "$${var.app_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "$${var.app_name}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "$${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "$${var.app_name}-public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "$${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "$${var.app_name}-public-subnet-2"
  }
}

# Private Subnets
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "$${var.aws_region}a"

  tags = {
    Name = "$${var.app_name}-private-subnet-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "$${var.aws_region}b"

  tags = {
    Name = "$${var.app_name}-private-subnet-2"
  }
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "$${var.app_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "main" {
  name       = "$${var.app_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_security_group" "rds" {
  name        = "$${var.app_name}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "$${var.app_name}-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "$${var.app_name}-db"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.rds_instance_class

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "viral_db"
  username = "postgres"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = var.enable_multi_az
  backup_retention_period = var.backup_retention

  skip_final_snapshot = false
  final_snapshot_identifier = "$${var.app_name}-db-snapshot"

  enable_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "$${var.app_name}-db"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "$${var.app_name}-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_security_group" "redis" {
  name        = "$${var.app_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "$${var.app_name}-redis-sg"
  }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "$${var.app_name}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  tags = {
    Name = "$${var.app_name}-redis"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "videos" {
  bucket = "$${var.app_name}-videos-$${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "$${var.app_name}-videos"
  }
}

resource "aws_s3_bucket" "uploads" {
  bucket = "$${var.app_name}-uploads-$${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "$${var.app_name}-uploads"
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "videos" {
  origin {
    domain_name = aws_s3_bucket.videos.bucket_regional_domain_name
    origin_id   = "S3Videos"
  }

  enabled = true

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Videos"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "$${var.app_name}-cloudfront"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
