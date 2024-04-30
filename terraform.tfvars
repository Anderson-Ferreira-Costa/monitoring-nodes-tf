region = "us-east-1"
function_name = "monitoring_nodes_eks_prd"

eventbridge_name        = "monitoring_nodes_eks_prd"
eventbridge_description = "Inicia o lambda monitoring_nodes_eks_prd a cada 5 minutos"
schedule_expression     = "cron(0/5 * * * ? *)"
