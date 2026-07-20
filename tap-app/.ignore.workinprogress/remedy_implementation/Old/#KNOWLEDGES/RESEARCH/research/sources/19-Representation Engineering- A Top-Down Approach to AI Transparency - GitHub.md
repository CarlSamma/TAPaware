> Source: https://github.com/andyzoujm/representation-engineering

GitHub - andyzoujm/representation-engineering: Representation Engineering: A Top-Down Approach to AI Transparency · GitHub
Skip to content
Navigation Menu
Toggle navigation 
Sign in
Appearance settings
Platform
AI CODE CREATION
GitHub Copilot Write better code with AI
GitHub Copilot app Direct agents from issue to merge
MCP Registry New Integrate external tools
DEVELOPER WORKFLOWS
Actions Automate any workflow
Codespaces Instant dev environments
Issues Plan and track work
Code Review Manage code changes
APPLICATION SECURITY
GitHub Advanced Security Find and fix vulnerabilities
Code security Secure your code as you build
Secret protection Stop leaks before they start
EXPLORE
Why GitHub
Documentation
Blog
Changelog
Marketplace View all features
Solutions
BY COMPANY SIZE
Enterprises
Small and medium teams
Startups
Nonprofits
BY USE CASE
App Modernization
DevSecOps
DevOps
CI/CD
View all use cases
BY INDUSTRY
Healthcare
Financial services
Manufacturing
Government
View all industries View all solutions
Resources
EXPLORE BY TOPIC
AI
Software Development
DevOps
Security
View all topics
EXPLORE BY TYPE
Customer stories
Events & webinars
Ebooks & reports
Business insights
GitHub Skills
SUPPORT & SERVICES
Documentation
Customer support
Community forum
Trust center
Partners View all resources
Open Source
COMMUNITY
GitHub Sponsors Fund open source developers
PROGRAMS
Security Lab
Maintainer Community
Accelerator
GitHub Stars
Archive Program
REPOSITORIES
Topics
Trending
Collections
Enterprise
ENTERPRISE SOLUTIONS
Enterprise platform AI-powered developer platform
AVAILABLE ADD-ONS
GitHub Advanced Security Enterprise-grade security features
Copilot for Business Enterprise-grade AI features
Premium Support Enterprise-grade 24/7 support
Pricing
Search or jump to...
Search code, repositories, users, issues, pull requests...
Search
Clear
Search syntax tips
Provide feedback
We read every piece of feedback, and take your input very seriously. [-]
Include my email address so I can be contacted
Cancel Submit feedback
Saved searches
Use saved searches to filter your results more quickly
Name
Query
To see all available qualifiers, see our documentation.
Cancel Create saved search
Sign in
Sign up
Appearance settings
Resetting focus
You signed in with another tab or window. Reload to refresh your session. You signed out in another tab or window. Reload to refresh your session. You switched accounts on another tab or window. Reload to refresh your session. Dismiss alert
andyzoujm / representation-engineering Public
Notifications You must be signed in to change notification settings
Fork 128
Star 1k
Code
Issues 25
Pull requests 1
Actions
Projects
Security and quality 0
Insights
Additional navigation options
Code
Issues
Pull requests
Actions
Projects
Security and quality
Insights 
andyzoujm/representation-engineering
main
5 Branches 5 Tags  
Go to file
Code
Open more actions menu
Folders and files
Repository files navigation
README
MIT license
Representation Engineering (RepE)
This is the official repository for " Representation Engineering: A Top-Down Approach to AI Transparency"
by Andy Zou, Long Phan, Sarah Chen, James Campbell, Phillip Guo, Richard Ren, Alexander Pan, Xuwang Yin, Mantas Mazeika, Ann-Kathrin Dombrowski, Shashwat Goel, Nathaniel Li, Michael J. Byun, Zifan Wang, Alex Mallen, Steven Basart, Sanmi Koyejo, Dawn Song, Matt Fredrikson, Zico Kolter, and Dan Hendrycks.
Check out our website and demo here. 
Introduction
In this paper, we introduce and characterize the emerging area of representation engineering (RepE), an approach to enhancing the transparency of AI systems that draws on insights from cognitive neuroscience. RepE places population-level representations, rather than neurons or circuits, at the center of analysis, equipping us with novel methods for monitoring and manipulating high-level cognitive phenomena in deep neural networks (DNNs). We provide baselines and an initial analysis of RepE techniques, showing that they offer simple yet effective solutions for improving our understanding and control of large language models. We showcase how these methods can provide traction on a wide range of safety-relevant problems, including truthfulness, memorization, power-seeking, and more, demonstrating the promise of representation-centered transparency research. We hope that this work catalyzes further exploration of RepE and fosters advancements in the transparency and safety of AI systems.
Installation
To install repe from the github repository main branch, run:
Quickstart
Our RepReading and RepControl pipelines inherit the 🤗 Hugging Face pipelines for both classification and generation.
RepReading and RepControl Experiments
Check out example frontiers of Representation Engineering (RepE), containing both RepControl and RepReading implementation. We welcome community contributions as well!
RepE_eval
We also release a language model evaluation framework RepE_eval based on RepReading that can serve as an additional baseline beside zero-shot and few-shot on standard benchmarks. Please check out our paper for more details.
Citation
If you find this useful in your research, please consider citing:
About
Representation Engineering: A Top-Down Approach to AI Transparency
www.ai-transparency.org/
Resources
Readme
License
MIT license
Uh oh!
There was an error while loading. Please reload this page.
Activity
Stars
1k stars
Watchers
27 watching
Forks
128 forks
Report repository
Releases 4
v0.1.4 Latest on Aug 13, 2024
+ 3 releases
Packages 0
No packages published
Uh oh!
There was an error while loading. Please reload this page.
Contributors 7
Languages
Jupyter Notebook 50.3%
Python 45.0%
Shell 4.7%
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
You can't perform that action at this time.