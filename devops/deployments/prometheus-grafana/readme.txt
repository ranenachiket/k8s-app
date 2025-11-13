===================================================================
### Installing only prometheus using Helm charts
===================================================================
Step 1: Add the Prometheus Community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

Step 2: Create namespace
kubectl create namespace monitoring

Step 3: Install Prometheus
helm install prometheus prometheus-community/prometheus --namespace monitoring

This installs:
Prometheus server
Alertmanager
Node exporters
Kube state metrics
Pushgateway

Step 4: Verify resources
kubectl get pods -n monitoring
kubectl get svc -n monitoring

Step 5: Expose service via Port-forwarding or ingress

option 1: port-forwarding
kubectl port-forward -n monitoring svc/prometheus-server 9090:80

option 2: via ingress controller kong or nginx
kubectl apply -f prometheus-ingress.yaml

===================================================================
### Installing prometheus and grafana using Helm (Recommended)
===================================================================
Step 1:
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

That chart includes:
Prometheus
Alertmanager
Node exporters
Grafana
CRDs (ServiceMonitor, PodMonitor, etc.)

Step 2:
Expose service via ingress controller kong or nginx
kubectl apply -f prometheus-ingress.yaml

Step 3:
Make sure update the nginx load balancer config file to listen for these domains:
e.g.
server {
    listen 80;
    server_name prometheus.kong.local grafana.kong.local;

ls -ltr /etc/nginx/conf.d/
total 12
-rw-r--r-- 1 root root  964 Nov  9 15:23 kong.conf
-rw-r--r-- 1 root root  985 Nov  9 15:25 argocd_kong.conf
-rw-r--r-- 1 root root 1016 Nov 12 13:48 prometheus_kong.conf


Step 4: access the prometheus and grafana domains.
Get the grafana default creds using the following
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

