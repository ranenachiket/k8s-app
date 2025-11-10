ArgoCD

https://www.youtube.com/watch?v=8AJlVQy6Cx0

Step 1: Create argocd namespace
kubectl create namespace argocd


Step 2: Install Argo CD
You can use kubectl or Helm

🅰️ Option 1 — Using kubectl (simplest)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml


———————————————————————————
🅱️ Option 2 — Using Helm (more flexible)
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd -n argocd


helm install argocd argo/argo-cd -n argocd
NAME: argocd
LAST DEPLOYED: Sat Nov  8 15:36:59 2025
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
In order to access the server UI you have the following options:

1. kubectl port-forward service/argocd-server -n argocd 8080:443

    and then open the browser on http://localhost:8080 and accept the certificate

2. enable ingress in the values file `server.ingress.enabled` and either
      - Add the annotation for ssl passthrough: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-1-ssl-passthrough
      - Set the `configs.params."server.insecure"` in the values file and terminate SSL at your ingress: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-2-multiple-ingress-objects-and-hosts

After reaching the UI the first time you can login with username: admin and the random password generated during the installation. You can find the password by running:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

(You should delete the initial secret afterwards as suggested by the Getting Started Guide: https://argo-cd.readthedocs.io/en/stable/getting_started/#4-login-using-the-cli)

—————————————————————————————————————
Step 3: Expose the Argo CD UI
Option A — Port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443
Then open in browser: https://localhost:8080

Option B — NodePort (if you prefer static access)
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
kubectl get svc argocd-server -n argocd

Note the NodePort (e.g. 32000), then open: https://<worker-node-ip>:<nodeport>

Step 4: Get the initial admin password
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d; echo
Username: admin

Step 5: Install argocd CLI
# Linux
sudo curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo chmod +x /usr/local/bin/argocd

Step 5: Login to argocd CLI
Then login via CLI:
argocd login localhost:8080 --username admin --password <your-password> --insecure


============================================================

Full cleanup and reinstall (recommended for local cluster)
This ensures a clean reset.

helm uninstall argocd -n argocd || true
kubectl delete ns argocd --wait=true
kubectl get crd | grep argoproj | awk '{print $1}' | xargs kubectl delete crd

============================================================

On the load balancer (rasp pi):

server {
    listen 80;
    server_name argocd.kong.local;

    location / {
        proxy_pass http://192.168.87.52:30080;
        proxy_set_header Host argocd.kong.local;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # generous timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout    120s;
        proxy_read_timeout    120s;

        # allow big responses
        proxy_buffering off;
    }
}


upstream argocd_gateway {
    # Kong NodePorts on each K8s node
    server 192.168.87.50:30080 max_fails=3 fail_timeout=10s;
    server 192.168.87.51:30080 max_fails=3 fail_timeout=10s;
    server 192.168.87.52:30080 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 80;
    server_name argocd.kong.local;

    # Optional health check endpoint
    location /health {
        return 200 "OK\n";
    }

    location / {
        proxy_pass http://argocd_gateway;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

    }
}



