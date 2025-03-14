# Introduction

## What is Feast?

Feast \(**Fea**ture **St**ore\) is an operational data system for managing and serving machine learning features to models in production.

![](.gitbook/assets/feast-architecture-diagrams%20%281%29%20%281%29%20%281%29%20%282%29%20%283%29%20%284%29%20%283%29%20%281%29%20%281%29%20%281%29%20%285%29.svg)

## Problems Feast Solves

**Models need consistent access to data:** ML systems built on traditional data infrastructure are often coupled to databases, object stores, streams, and files. A result of this coupling, however, is that any change in data infrastructure may break dependent ML systems. Another challenge is that dual implementations of data retrieval for training and serving can lead to inconsistencies in data, which in turn can lead to training-serving skew.

Feast decouples your models from your data infrastructure by providing a single data access layer that abstracts feature storage from feature retrieval. Feast also provides a consistent means of referencing feature data for retrieval, and therefore ensures that models remain portable when moving from training to serving.

**Deploying new features into production is difficult:** Many ML teams consist of members with different objectives. Data scientists, for example, aim to deploy features into production as soon as possible, while engineers want to ensure that production systems remain stable. These differing objectives can create an organizational friction that slows time-to-market for new features.

Feast addresses this friction by providing both a centralized registry to which data scientists can publish features, and a battle-hardened serving layer. Together, these enable non-engineering teams to ship features into production with minimal oversight.

**Models need point-in-time correct data:** ML models in production require a view of data consistent with the one on which they are trained, otherwise the accuracy of these models could be compromised. Despite this need, many data science projects suffer from inconsistencies introduced by future feature values being leaked to models during training.

Feast solves the challenge of data leakage by providing point-in-time correct feature retrieval when exporting feature datasets for model training.

**Features aren't reused across projects:** Different teams within an organization are often unable to reuse features across projects. The siloed nature of development and the monolithic design of end-to-end ML systems contribute to duplication of feature creation and usage across teams and projects.

Feast addresses this problem by introducing feature reuse through a centralized system \(a registry\). This registry enables multiple teams working on different projects not only to contribute features, but also to reuse these same features. With Feast, data scientists can start new ML projects by selecting previously engineered features from a centralized registry, and are no longer required to develop new features for each project.

## Problems Feast does not yet solve

**Feature engineering:** We aim for Feast to support light-weight feature engineering as part of our API.

**Feature discovery:** We also aim for Feast to include a first-class user interface for exploring and discovering entities and features.

**‌Feature validation:** We additionally aim for Feast to improve support for statistics generation of feature data and subsequent validation of these statistics. Current support is limited.

## What Feast is not

[**ETL**](https://en.wikipedia.org/wiki/Extract,_transform,_load) **or** [**ELT**](https://en.wikipedia.org/wiki/Extract,_load,_transform) **system:** Feast is not \(and does not plan to become\) a general purpose data transformation or pipelining system. Feast plans to include a light-weight feature engineering toolkit, but we encourage teams to integrate Feast with upstream ETL/ELT systems that are specialized in transformation.

**Data warehouse:** Feast is not a replacement for your data warehouse or the source of truth for all transformed data in your organization. Rather, Feast is a light-weight downstream layer that can serve data from an existing data warehouse \(or other data sources\) to models in production.

**Data catalog:** Feast is not a general purpose data catalog for your organization. Feast is purely focused on cataloging features for use in ML pipelines or systems, and only to the extent of facilitating the reuse of features.

## How can I get started?

{% hint style="info" %}
The best way to learn Feast is to use it. Head over to our [Quickstart](feast-on-kubernetes/getting-started/install-feast/quickstart.md) and try out our examples!
{% endhint %}

Explore the following resources to get started with Feast:

* [Getting Started](feast-on-kubernetes/getting-started/) provides guides on [Installing Feast](feast-on-kubernetes/getting-started/install-feast/) and [Connecting to Feast](feast-on-kubernetes/getting-started/connect-to-feast/).
* [Concepts](feast-on-kubernetes/concepts/overview.md) describes all important Feast API concepts.
* [User guide](feast-on-kubernetes/user-guide/define-and-ingest-features.md) provides guidance on completing Feast workflows.
* [Examples](https://github.com/feast-dev/feast/tree/master/examples) contains a Jupyter notebook that you can run on your Feast deployment.
* [Advanced](feast-on-kubernetes/advanced-1/troubleshooting.md) contains information about both advanced and operational aspects of Feast.
* [Reference](feast-on-kubernetes/reference-1/api/) contains detailed API and design documents for advanced users.
* [Contributing](contributing/contributing.md) contains resources for anyone who wants to contribute to Feast.

