===================================
Kong Installation Steps
===================================
Step 1: Install Kong with the Ingress Controller enabled
helm repo add kong https://charts.konghq.com
helm repo update

helm install kong kong/kong \
  --namespace kong \
  --set ingressController.installCRDs=false \
  --set proxy.type=NodePort \
  --set proxy.http.nodePort=30080 \
  --set proxy.tls.enabled=false \
  --set env.database=off \
  --set ingressController.enabled=true \
  --set replicaCount=1


===================================

Verify proxy logs on kong (traffic coming from lodging balancer rasp to kong):
kubectl logs -n kong kong-kong-787b7798d8-xljw7 -c proxy -f

