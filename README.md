# K8S Intro

This is a basic walk-through over some basic k8s concepts as well as some tools commonly used to
deploy apps.

Before starting we need to install these tools:

* [docker](https://docs.docker.com/get-docker/)
* [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
* [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
* [helm](https://helm.sh/docs/intro/install/)

## Setup

To be able to play around we need to spin up a local k8s cluster. We'll use
[kind](https://kind.sigs.k8s.io/) to create the cluster and
[ingress-nginx](https://kubernetes.github.io/ingress-nginx/) as an ingress-controller to be able to
access our app from outside the cluster.
This setup was took from the [kind page](https://kind.sigs.k8s.io/docs/user/ingress/),
so kudos to them :)

### Cluster

Let's start creating the cluster by running

```bash
kind create cluster --config assets/kind-config.yaml
```

This command will create a three node cluster with one control-plane node and two workers.

### Ingress-controller

Once the cluster is up-and-running the next step is to be able to access our apps from outside. The
ingress-controller will do the work, we just need to run

```bash
kubectl apply -f assets/ingress-controller.yaml
```

This command will create all the necessary resources to handle external requests and forward them to
the proper service.

### Exposing our app

So the ingress-controller will route the traffic, but we need to tell it where to route it. How an
ingress work is beyond the scope of this guide. We'll just run this command

```bash
kubectl apply -f k8s/ingress.yaml
```

## Building our app

We'll build a really simple python app with 3 endpoints:

* `/whoami`: Will return the hostname the app is running in
* `/fail`: Will make our app fail (exit with status 1)
* `/db`: Will connect to a MySQL DB and show its version

Here we took advantage of [GitHub Actions](https://github.com/features/actions) to automatically
build and push our app to Dockerhub on any change to the Dockerfile or the app code in the main
branch.

If you want to build your image locally please run this command

```bash
docker build . -t k8s-app
```

## Configuring our app



```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
```

## Running our app

After our app is built we need to run it somewhere. Let's go through different ways of doing so and
see the benefits of using a container orchestrator.

### Single container outside k8s

First of all, let's run our app as a standalone container using docker.

```bash
docker run -d -p 5000:5000 lucasgiaco91/k8s-app
```

Our app is up-and-running and that's awesome! If you curl it at `localhost:5000/whoami` you'll get
the container ID.

As we know if anything could go wrong it will go wrong. So, let's curl at `localhost:5000/fail` and
see that the container ends unexpectedly. If this happens in a productive environment our app will
offline until we manually restart it.

It would be great if someone or something automatically restart our container any time it fails
right? Here is when kubernetes comes in.

### Standalone pod

The minimum execution unit in Kubernetes is a
[pod](https://kubernetes.io/docs/concepts/workloads/pods/). A pod is a group of one or more
containers that runs simultaneously. Let's run our container inside a pod and see how it comes.

```bash
kubectl apply -f k8s/pod.yaml
```

It's important to notice the `restartPolicy: Always` line in the pod declaration.

```bash
kubectl apply -f k8s/svc.yaml
```

### Deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

## External dependencies

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install mysql bitnami/mysql --set auth.rootPassword=R00t! -n db --create-namespace --wait
```

This may take several minutes before being ready

## Tear down

Once you're done playing with the local k8s cluster just run this command to delete the cluster

```bash
kind delete cluster --name local
```
