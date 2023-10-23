{{/*
Expand the name of the chart.
*/}}
{{- define "sae.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sae.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sae.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sae.labels" -}}
helm.sh/chart: {{ include "sae.chart" . }}
{{ include "sae.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sae.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sae.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sae.serviceAccountName" -}}
{{- include "sae.fullname" . }}
{{- end }}

{{/*
Derive redis service name
*/}}
{{- define "sae.redisServiceName" -}}
{{- printf "%s-%s" .Release.Name "redis-master" -}}
{{- end }}

{{/*
Derive redis metrics service name
*/}}
{{- define "sae.redisMetricsServiceName" -}}
{{- printf "%s-%s" .Release.Name "redis-metrics" -}}
{{- end }}

{{/*
Hard-code Redis service port (for now)
*/}}
{{- define "sae.redisServicePort" -}}
"6379"
{{- end }}

{{/*
Derive redis metrics service name
*/}}
{{- define "sae.nodeExporterServiceName" -}}
{{- printf "%s-%s" .Release.Name "nodeexporter" -}}
{{- end }}

{{/*
Derive prometheus service name
*/}}
{{- define "sae.prometheusServiceName" -}}
{{- printf "%s-%s" .Release.Name "prometheus-server" -}}
{{- end }}
