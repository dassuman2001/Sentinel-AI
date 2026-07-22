resource "aws_db_subnet_group" "rds" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.project_name}-rds-subnet-group"
  }
}

resource "aws_db_instance" "mysql" {
  identifier             = "${var.project_name}-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp2"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"  # Free-tier eligible class
  db_name                = "sentinel_db"
  username               = "sentinel_user"
  password               = var.db_password
  parameter_group_name   = "default.mysql8.0"
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  multi_az               = false          # Must be false for Free Tier eligibility

  tags = {
    Name = "${var.project_name}-rds-mysql"
  }
}

variable "db_password" {
  type        = string
  default     = "sentinel_password"
  sensitive   = true
  description = "Production MySQL Database Password"
}

output "rds_endpoint" {
  value       = aws_db_instance.mysql.endpoint
  description = "Connection endpoint of the RDS MySQL Instance"
}
