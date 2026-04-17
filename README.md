# CAP6640 Project

This repository contains the codebase for the CAP6640 project, structured into two main directories:

## `data-curation-code`
This folder contains the scripts and tools used for generating and curating the dataset. This includes code to introduce controlled perturbations (like typos, grammatical errors, and language discrepancies) into prompts, generating various intensity levels of prompt errors (low, medium, high). 

## `inference-code`
This folder handles the model inference pipeline. It is responsible for taking the different sets of curated datasets (including perturbed and control prompts) and running them through the relevant models to generate or evaluate outputs.
