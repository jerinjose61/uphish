<h1>Introduction</h1>
<p>
Uphish is a platform to conduct Phishing Simulation Campaigns.
Phishing campaigns are basically mock phishing attacks on your employees.
The primary objective is to make the employees aware about phishing attacks and the resulting damages.
It also helps the security team measure the effectiveness of their training over time.
</p>

<p>
With Uphish you can:
  <ul>
    <li>Send phishing emails to employees</li>
    <li>Track how many employees opened the email</li>
    <li>Track how many employees clicked on the phishing link</li>
    <li>Track how many employees submitted data through the phishing page</li>
    <li>Track how many people reported the phishing attack</li>
  </ul>
</p>

<hr>

<h1>Architecture</h1>
<p>
The Uphish platform consists of:
  <ul>
    <li>Uphish Management Console (UMC)</li>
    <li>Uphish Phishing Apps (UPAs)</li>
  </ul>
</p>

<h2>Uphish Management Console (UMC)</h2>
<p>
The UMC is the main application using which you conduct the phishing campaigns.

Here, you can:
  <ul>
    <li>Specify the details of the SMTP Server using which we will send the phishing email</li>
    <li>Specify the details of the target employees</li>
    <li>Design the phishing emails</li>
    <li>Specify the URL of the phishing pages</li>
  </ul>
</p>

<h2>Uphish Phishing Apps (UPAs)</h2>
<p>
The UPAs are the phishing pages (a.k.a Landing Pages) to where the employees will be redirected to when they click the link in the phishing email.

The primary job of the UPA is to:
  <ul>
    <li>Serve the phishing page</li>
    <li>Tell the UMC that the employee has clicked the link through an API</li>
    <li>Transfer the information (such as Username & Password) entered by the employee in the phishing page to the UMC for secure storage through an API</li>
  </ul>

You can develop the UPAs using any programming language / framework.
It just needs to make API calls to the UMC. As standard examples, a few UPAs developed using Flask are provided.
Please check the references section for the same.
</p>

<h1>References</h1>
<ul>
  <li><a href="https://drive.google.com/file/d/1PpZpOoHHfV4xjOHXjbpMgxlbMoBW8_3l/view?usp=sharing">Uphish User Guide</a></li>
  <li><a href="https://drive.google.com/file/d/1Cp1Axg1qMdJtP8xs4UeUiADAsWfWHJQp/view?usp=sharing">UMC Deployment Guide</a></li>
  <li><a href="https://drive.google.com/file/d/1hYPQk_AOjxg1MB0pSLHFOsfxsONLbj-c/view?usp=sharing">UPA Development Guide</a></li>
  <li><a href="https://github.com/jerinjose61/upa-flask">Sample Flask UPAs</a></li>
  <li><a href="https://github.com/jerinjose61/uphish-email-templates">Sample HTML Email Templates</a></li>
</ul>
