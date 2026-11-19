{{/*
releaseboard.name returns the short chart name, unless nameOverride is provided.
*/}}
{{- define "releaseboard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
releaseboard.fullname returns a release-specific name that stays within Kubernetes' 63-character limit.
*/}}
{{- define "releaseboard.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
releaseboard.labels adds standard Kubernetes metadata to every chart resource.
*/}}
{{- define "releaseboard.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "releaseboard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
releaseboard.selectorLabels returns stable labels used by Deployment and Service selectors.
*/}}
{{- define "releaseboard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "releaseboard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
