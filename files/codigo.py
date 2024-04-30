import boto3
from datetime import datetime, timedelta

ddb_client = boto3.client('dynamodb')
ddb_table_name = 'InstanceAlertStateTable'

def get_instance_alert_state(instance_id):
    try:
        response = ddb_client.get_item(
            TableName=ddb_table_name,
            Key={'InstanceId': {'S': instance_id}}
        )
        return response.get('Item', None)
    except ddb_client.exceptions.ResourceNotFoundException:
        return None

def update_instance_alert_state(instance_id, last_alert_time):
    ddb_client.put_item(
        TableName=ddb_table_name,
        Item={
            'InstanceId': {'S': instance_id},
            'LastAlertTime': {'S': last_alert_time}
        }
    )

def send_sns_notification(subject, message, notification_type):
    sns_client = boto3.client('sns')
    sns_topic_arn = 'arn:aws:sns:us-east-1:525314794516:CloudWatch-Alarms-AmazonMQ'
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=message,
        MessageAttributes={
            'notification_type': {
                'DataType': 'String',
                'StringValue': notification_type
            }
        }
    )

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    cloudwatch_client = boto3.client('cloudwatch')

    tag_key = 'Name'
    tag_value = 'SINAPSE-EKS-PRD'

    response = ec2_client.describe_instances(
        Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            last_alert_state = get_instance_alert_state(instance_id)
            if last_alert_state:
                last_alert_time = datetime.strptime(last_alert_state['LastAlertTime']['S'], '%Y-%m-%dT%H:%M:%S.%f')
                if datetime.utcnow() - last_alert_time < timedelta(minutes=60):
                    continue  # Se um alerta foi enviado há menos de 60 minutos, não envie outro
            auto_scaling_group_name = None
            image_id = instance['ImageId']
            instance_type = instance['InstanceType']
            for tag in instance['Tags']:
                if tag['Key'] == 'aws:autoscaling:groupName':
                    auto_scaling_group_name = tag['Value']
                    break

            # Obtendo métricas de CPU nas últimas 5 minutos
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)

            # Consultando métricas de CPU, disco e memória...
            cpu_metric_data = cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'cpu_usage',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EC2',
                                'MetricName': 'CPUUtilization',
                                'Dimensions': [
                                    {
                                        'Name': 'InstanceId',
                                        'Value': instance_id
                                    }
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Average'
                        },
                        'ReturnData': True
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                ScanBy='TimestampDescending'
            )

            # Extraindo dados de cpu
            cpu_data = cpu_metric_data['MetricDataResults'][0]['Values']
            
            print("Instance Id:", instance_id)
            print("CPU Data:", cpu_data)

            # Métricas de disco
            disk_metric_data = cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'disk_usage',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'CWAgent',
                                'MetricName': 'Disk_utilization',
                                'Dimensions': [
                                    {
                                        'Name': 'path',
                                        'Value': '/'
                                    },
                                    {
                                        'Name': 'InstanceId',
                                        'Value': instance_id
                                    },
                                    {
                                        'Name': 'AutoScalingGroupName',
                                        'Value': auto_scaling_group_name
                                    },
                                    {
                                        'Name': 'ImageId',
                                        'Value': image_id
                                    },
                                    {
                                        'Name': 'InstanceType',
                                        'Value': instance_type
                                    },
                                    {
                                        'Name': 'device',
                                        'Value': 'nvme0n1p1'
                                    },
                                    {
                                        'Name': 'fstype',
                                        'Value': 'xfs'
                                    }
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Maximum'
                        },
                        'ReturnData': True
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                ScanBy='TimestampDescending'
            )
            
            # Extraindo dados de disco
            disk_data = disk_metric_data['MetricDataResults'][0]['Values']
            
            print("Disk Data:", disk_data)
            
            # Métricas de memória
            memory_metric_data = cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'disk_usage',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'CWAgent',
                                'MetricName': 'Memory_utilization',
                                'Dimensions': [
                                    {
                                        'Name': 'InstanceId',
                                        'Value': instance_id
                                    },
                                    {
                                        'Name': 'AutoScalingGroupName',
                                        'Value': auto_scaling_group_name
                                    },
                                    {
                                        'Name': 'ImageId',
                                        'Value': image_id
                                    },
                                    {
                                        'Name': 'InstanceType',
                                        'Value': instance_type
                                    }
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Average'
                        },
                        'ReturnData': True
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                ScanBy='TimestampDescending'
            )
            
            # Extraindo dados de disco
            memory_data = memory_metric_data['MetricDataResults'][0]['Values']
            
            print("Memory Data:", memory_data)
            
            # thresholds
            high_threshold_percentage_cpu = 80
            low_threshold_percentage_cpu = 10
            high_threshold_percentage_disk = 70
            high_threshold_percentage_memory = 80
            account = "Sinapse PRD"
            
            email_messages = []

            # Verifica se a utilização de CPU excede o limite.
            if cpu_data and max(cpu_data) > high_threshold_percentage_cpu:
                cpu_utilization = round(cpu_data[0], 0)
                message_cpu = f'O uso de cpu excedeu {high_threshold_percentage_cpu}%, utilização atual {cpu_utilization}%.'
                email_messages.append((message_cpu))

            # Verifica se a utilização de CPU está abaixo do limite.
            elif cpu_data and min(cpu_data) < low_threshold_percentage_cpu:
                cpu_utilization = round(cpu_data[0], 0)
                message_cpu = f'O uso de CPU está abaixo de {low_threshold_percentage_cpu}%, utilização atual {cpu_utilization}%.'
                email_messages.append((message_cpu))

            # Verifica se a utilização de disco excede o limite.
            if disk_data and max(disk_data) > high_threshold_percentage_disk:
                disk_utilization = round(disk_data[0], 0)
                message_disk = f'O uso de disco excedeu {high_threshold_percentage_disk}%, utilização atual {disk_utilization}%.'
                email_messages.append((message_disk))
            
            # Verifica se a utilização de memória excede o limite.
            if memory_data and max(memory_data) > high_threshold_percentage_memory:
                memory_utilization = round(memory_data[0], 0)
                message_memory  = f'O uso de memória excedeu {high_threshold_percentage_memory}%, utilização atual {memory_utilization}%.'
                email_messages.append((message_memory))
                
            if email_messages:
                email_subject = f'{account} - alerta da ec2: {instance_id}'
                email_messages = '\n\n'.join(email_messages)
                send_sns_notification(email_subject, email_messages, 'high')
                update_instance_alert_state(instance_id, end_time.isoformat()) 

    return {'statusCode': 200, 'body': 'Métricas obtidas com sucesso.'}
