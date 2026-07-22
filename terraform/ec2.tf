data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_key_pair" "ssh_key" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

variable "ssh_public_key" {
  type        = string
  description = "Public SSH Key to access the EC2 instance"
}

resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = "t3.micro" # Free-tier eligible class
  subnet_id              = aws_subnet.public_1.id
  key_name               = aws_key_pair.ssh_key.key_name
  vpc_security_group_ids = [aws_security_group.ec2.id]

  user_data = <<-EOF
              #!/bin/bash
              # Update and Install Docker and Git
              yum update -y
              amazon-linux-extras install docker -y
              yum install -y git
              service docker start
              systemctl enable docker
              usermod -a -G docker ec2-user

              # Install Docker Compose v2
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64" -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
              ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/bin/docker-compose

              # Clone the repository
              cd /home/ec2-user
              git clone https://github.com/dassuman2001/Sentinel-AI.git
              cd Sentinel-AI

              # Create production .env config
              cat <<ENV_FILE > backend/.env
              DATABASE_URL=mysql+pymysql://sentinel_user:${var.db_password}@${aws_db_instance.mysql.endpoint}/sentinel_db
              REDIS_URL=redis://redis:6379/0
              SECRET_KEY=supersecretkeyforprodchangeinprod123456
              GOOGLE_CLIENT_ID=${var.google_client_id}
              GOOGLE_CLIENT_SECRET=${var.google_client_secret}
              AUTH0_DOMAIN=${var.auth0_domain}
              AUTH0_CLIENT_ID=${var.auth0_client_id}
              ENV_FILE

              # Launch the app using committed production configuration
              docker-compose -f docker-compose.prod.yml up --build -d
              EOF

  tags = {
    Name = "${var.project_name}-ec2-instance"
  }
}

# Elastic IP for consistent endpoint routing
resource "aws_eip" "eip" {
  instance = aws_instance.app_server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

# Application Load Balancer
resource "aws_lb" "alb" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = {
    Name = "${var.project_name}-alb"
  }
}

resource "aws_lb_target_group" "tg" {
  name        = "${var.project_name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    path                = "/api/v1/dashboard/stats"
    port                = "8000"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200,401" # 401 is allowed because of auth token requirement
  }
}

resource "aws_lb_target_group_attachment" "attachment" {
  target_group_arn = aws_lb_target_group.tg.arn
  target_id        = aws_instance.app_server.id
  port             = 8000
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

variable "google_client_id" {
  type        = string
  default     = ""
  description = "Google OAuth Client ID"
}

variable "google_client_secret" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Google OAuth Client Secret"
}

variable "auth0_domain" {
  type        = string
  default     = ""
  description = "Auth0 Domain"
}

variable "auth0_client_id" {
  type        = string
  default     = ""
  description = "Auth0 Client ID"
}

output "load_balancer_dns" {
  value       = aws_lb.alb.dns_name
  description = "Public Load Balancer DNS to connect to backend APIs"
}
