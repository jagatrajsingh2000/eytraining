# HealthBridge Azure Routing Solution

## Problem Statement

HealthBridge has **six routing requirements**.
We need to classify each requirement as either:

- **Azure Application Gateway**
- **Azure Load Balancer**

Use **Application Gateway** when traffic is **HTTP/HTTPS Layer 7** and needs URL routing, hostname routing, header routing, WAF, or SSL/TLS handling.

Use **Load Balancer** when traffic is **TCP/UDP Layer 4**, internal, low latency, no HTTP inspection, or simple failover.

## Solution Matrix with Requirements

| # | Requirement | Word-to-word requirement | Classification | Key deciding factor |
|---|---|---|---|---|
| 1 | Patient web portal | **Patient web portal — public HTTPS traffic**. The patient-facing web app **(React SPA + REST API)** receives up to **400,000 requests/hour** from browsers. The team needs **SSL termination at the entry point**, **WAF protection against OWASP Top 10 attacks** `(SQL injection, XSS)`, and the ability to route **/api/*** to the API backend pool and **/static/*** to Azure Blob Storage — all on port **443**. | **Application Gateway** | Public HTTPS traffic needs **WAF**, **SSL termination**, and **URL/path-based routing**. These are Layer 7 features. |
| 2 | Clinical API internal | **Clinical API — internal hospital traffic**. Hospital EHR systems within the Azure VNet send **HL7 FHIR requests over TCP port 8443** to a pool of **12 Clinical API VMs**. Traffic is entirely internal — **no public internet exposure**. The team needs simple, fast distribution across the VM pool with **sub-millisecond overhead**. No HTTP inspection, WAF, or path routing is required. | **Load Balancer** | Internal VNet-only **TCP** traffic. No HTTP awareness, WAF, or path routing needed. |
| 3 | DICOM image streaming | **Diagnostic image streaming — large TCP payloads**. Radiologists stream **DICOM images** `(50–200 MB per study)` from radiology workstations inside the hospital network to a pool of image-processing VMs. Traffic is **raw TCP, not HTTP**. Connections are **long-lived** `(minutes per session)` and must be pinned to the same backend VM for the entire transfer to preserve session state. No content inspection needed. | **Load Balancer** | Raw non-HTTP TCP traffic with long-lived connections and session persistence. Layer 4 is enough. |
| 4 | Auth service header routing | **Authentication service — multi-tenant header routing**. HealthBridge serves **14 NHS trusts**, each with its own identity provider. The auth service must inspect the **x-Trust-ID HTTP header** on every login request and route it to the correct trust-specific backend pool, for example **Trust-ID: NW01 → North West pool**. Each pool runs a separate **SAML federation config**. SSL must be re-encrypted end-to-end. | **Application Gateway** | Needs HTTP **header-based routing** and end-to-end TLS. This requires Layer 7. |
| 5 | Legacy SOAP lab service | **Legacy lab results SOAP service**. An ageing **SOAP/XML service** runs on two VMs inside the VNet and is called exclusively by internal pathology lab systems over **TCP port 9090**. The vendor contract forbids any modification to the payload or headers. The team simply needs redundancy — if one VM goes down, traffic must failover to the other. No SSL offload, no content inspection, minimal configuration. | **Load Balancer** | Internal TCP service. Only simple redundancy/failover is needed. No payload or header inspection. |
| 6 | Admin dashboard hostname | **Admin dashboard — host-based routing + autoscale**. The admin dashboard **(admin.healthbridge.nhs.uk)** and the public portal **([www.healthbridge.nhs.uk](http://www.healthbridge.nhs.uk))** share a single public IP. Traffic must be split by hostname: admin subdomain → **2-VM admin pool**; www subdomain → **6-VM public pool**. The admin pool should also have autoscaling rules tied to CPU. Both are HTTPS. | **Application Gateway** | Needs HTTPS **host-based routing** on the same public IP. This is Layer 7 routing. |

## Final Simple Answer

| # | Requirement | Use | Simple reason |
|---|---|---|---|
| 1 | Patient web portal | **Application Gateway** | Because it needs WAF, SSL termination, and URL routing. |
| 2 | Clinical API internal | **Load Balancer** | Because it is internal TCP traffic and does not need HTTP features. |
| 3 | DICOM image streaming | **Load Balancer** | Because it is raw TCP with large files and long sessions. |
| 4 | Auth service header routing | **Application Gateway** | Because it needs to read HTTP headers and route by `x-Trust-ID`. |
| 5 | Legacy SOAP lab service | **Load Balancer** | Because it only needs simple internal TCP failover. |
| 6 | Admin dashboard hostname | **Application Gateway** | Because it needs hostname-based HTTPS routing. |

## One-Line Rule

**Application Gateway = smart HTTP/HTTPS router.**

**Load Balancer = fast TCP/UDP traffic distributor.**
