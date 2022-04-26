#! /bin/bash

export AWS_PROFILE=personal

name=openfaas-eks-5

# Create cluster
eksctl create cluster --name=$name --nodes=2 --auto-kubeconfig --region=us-west-2

# Check that it is created
export KUBECONFIG=~/.kube/eksctl/clusters/$name
kubectl get nodes

# Install helm on cluster
kubectl -n kube-system create sa tiller
kubectl create clusterrolebinding tiller-cluster-rule \
    --clusterrole=cluster-admin \
    --serviceaccount=kube-system:tiller 

helm init --upgrade --service-account tiller

# Create kubernetes namespaces
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml

# Setup authentication
echo "Password: saaf_open_faas_password"

kubectl -n openfaas create secret generic basic-auth \
    --from-literal=basic-auth-user=admin \
    --from-literal=basic-auth-password=saaf_open_faas_password

# Deploy OpenFaaS
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update

export TIMEOUT=3m

helm upgrade openfaas --install openfaas/openfaas \
    --namespace openfaas  \
    --set functionNamespace=openfaas-fn \
    --set serviceType=LoadBalancer \
    --set basic_auth=true \
    --set operator.create=true \
    --set gateway.replicas=2 \
    --set queueWorker.replicas=2 \
    --set gateway.upstreamTimeout=$TIMEOUT \
    --set gateway.writeTimeout=$TIMEOUT \
    --set gateway.readTimeout=$TIMEOUT \
    --set faasnetes.writeTimeout=$TIMEOUT \
    --set faasnetes.readTimeout=$TIMEOUT \
    --set queueWorker.ackWait=$TIMEOUT


# Check if deployed:
echo "Check if deployed, repeat until all is 1"
echo "Command: kubectl --namespace=openfaas get deployments -l \"release=openfaas, app=openfaas\""
kubectl --namespace=openfaas get deployments -l "release=openfaas, app=openfaas"









echo "Waiting 5 minutes... Hopefully that is enough time."
sleep 300

kubectl get svc -n openfaas -o wide

export OPENFAAS_URL=$(kubectl get svc -n openfaas gateway-external -o  jsonpath='{.status.loadBalancer.ingress[*].hostname}'):8080  \
&& echo Your gateway URL is: $OPENFAAS_URL

echo saaf_open_faas_password | faas-cli login --username admin --password-stdin

faas-cli store deploy NodeInfo