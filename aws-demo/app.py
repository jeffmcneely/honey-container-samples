#!/usr/bin/env python3
"""
AWS VPC and EC2 Resource Tree Visualization
Uses Rich library to display VPCs, EC2 instances, interfaces, and gateways
"""

import boto3
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from botocore.exceptions import ClientError, NoCredentialsError
import sys


def get_vpc_tree():
    """Build a tree structure of AWS VPC resources"""
    try:
        # Initialize AWS clients
        ec2 = boto3.client('ec2')
        console = Console()
        
        # Create root tree
        tree = Tree("🌐 [bold cyan]AWS VPC Resources[/bold cyan]")
        
        # Get all VPCs
        vpcs_response = ec2.describe_vpcs()
        vpcs = vpcs_response.get('Vpcs', [])
        
        if not vpcs:
            console.print("[yellow]No VPCs found in the current region[/yellow]")
            return tree
        
        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr = vpc.get('CidrBlock', 'N/A')
            is_default = vpc.get('IsDefault', False)
            
            # Get VPC name from tags
            vpc_name = 'N/A'
            if 'Tags' in vpc:
                for tag in vpc['Tags']:
                    if tag['Key'] == 'Name':
                        vpc_name = tag['Value']
                        break
            
            # Create VPC branch
            vpc_label = f"🏢 VPC: {vpc_name} ({vpc_id})"
            if is_default:
                vpc_label += " [yellow](Default)[/yellow]"
            vpc_label += f" - {cidr}"
            
            vpc_branch = tree.add(f"[bold green]{vpc_label}[/bold green]")
            
            # Get Internet Gateways
            igw_response = ec2.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )
            igws = igw_response.get('InternetGateways', [])
            
            if igws:
                igw_branch = vpc_branch.add("🌍 [bold blue]Internet Gateways[/bold blue]")
                for igw in igws:
                    igw_id = igw['InternetGatewayId']
                    igw_name = 'N/A'
                    if 'Tags' in igw:
                        for tag in igw['Tags']:
                            if tag['Key'] == 'Name':
                                igw_name = tag['Value']
                                break
                    igw_branch.add(f"[blue]IGW: {igw_name} ({igw_id})[/blue]")
            
            # Get NAT Gateways
            ngw_response = ec2.describe_nat_gateways(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            ngws = ngw_response.get('NatGateways', [])
            
            if ngws:
                ngw_branch = vpc_branch.add("🔀 [bold magenta]NAT Gateways[/bold magenta]")
                for ngw in ngws:
                    ngw_id = ngw['NatGatewayId']
                    state = ngw['State']
                    subnet_id = ngw.get('SubnetId', 'N/A')
                    ngw_name = 'N/A'
                    if 'Tags' in ngw:
                        for tag in ngw['Tags']:
                            if tag['Key'] == 'Name':
                                ngw_name = tag['Value']
                                break
                    
                    state_color = "green" if state == "available" else "yellow"
                    ngw_branch.add(
                        f"[magenta]NGW: {ngw_name} ({ngw_id})[/magenta] - "
                        f"[{state_color}]{state}[/{state_color}] - Subnet: {subnet_id}"
                    )
            
            # Get EC2 Instances
            instances_response = ec2.describe_instances(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            instances = []
            for reservation in instances_response.get('Reservations', []):
                instances.extend(reservation.get('Instances', []))
            
            if instances:
                instances_branch = vpc_branch.add("💻 [bold yellow]EC2 Instances[/bold yellow]")
                
                for instance in instances:
                    instance_id = instance['InstanceId']
                    instance_type = instance.get('InstanceType', 'N/A')
                    state = instance['State']['Name']
                    private_ip = instance.get('PrivateIpAddress', 'N/A')
                    
                    # Get instance name from tags
                    instance_name = 'N/A'
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                                break
                    
                    # Color based on state
                    state_colors = {
                        'running': 'green',
                        'stopped': 'red',
                        'pending': 'yellow',
                        'stopping': 'yellow',
                        'terminated': 'dim'
                    }
                    state_color = state_colors.get(state, 'white')
                    
                    instance_label = (
                        f"[yellow]Instance: {instance_name} ({instance_id})[/yellow] - "
                        f"{instance_type} - [{state_color}]{state}[/{state_color}] - {private_ip}"
                    )
                    instance_branch = instances_branch.add(instance_label)
                    
                    # Get network interfaces for this instance
                    if 'NetworkInterfaces' in instance:
                        if instance['NetworkInterfaces']:
                            eni_branch = instance_branch.add("🔌 [cyan]Network Interfaces[/cyan]")
                            
                            for eni in instance['NetworkInterfaces']:
                                eni_id = eni.get('NetworkInterfaceId', 'N/A')
                                eni_ip = eni.get('PrivateIpAddress', 'N/A')
                                subnet_id = eni.get('SubnetId', 'N/A')
                                public_ip = eni.get('Association', {}).get('PublicIp', 'N/A')
                                
                                eni_label = f"[cyan]ENI: {eni_id}[/cyan] - IP: {eni_ip}"
                                if public_ip != 'N/A':
                                    eni_label += f" - Public IP: {public_ip}"
                                eni_label += f" - Subnet: {subnet_id}"
                                
                                eni_branch.add(eni_label)
            else:
                vpc_branch.add("[dim]No EC2 instances found[/dim]")
        
        return tree
        
    except NoCredentialsError:
        console.print("[bold red]Error:[/bold red] AWS credentials not found.")
        console.print("Please configure AWS credentials using one of these methods:")
        console.print("  1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        console.print("  2. AWS credentials file (~/.aws/credentials)")
        console.print("  3. IAM role (if running on EC2)")
        sys.exit(1)
    except ClientError as e:
        console.print(f"[bold red]AWS Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def main():
    """Main function to display AWS VPC tree"""
    console = Console()
    
    # Get AWS region
    session = boto3.session.Session()
    region = session.region_name or 'us-east-1'
    
    console.print(Panel.fit(
        f"[bold]AWS VPC Resource Tree[/bold]\n"
        f"Region: [cyan]{region}[/cyan]",
        border_style="blue"
    ))
    console.print()
    
    # Build and display the tree
    tree = get_vpc_tree()
    console.print(tree)
    console.print()


if __name__ == "__main__":
    main()
