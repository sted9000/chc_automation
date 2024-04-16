# CHC Automation


## Description
Workflow to automate converting service provider's reports into a daily summary email for a small business.

## General
### Problem
Many small and medium-sized businesses use third party services handles various aspects of their business. These services often provide daily reports that are useful for the business owner to monitor the health of their business. However, these reports are typically in a format that is not easily consumable -- leaving the business owner to sift through multiple pages to extract a single piece of relevant information.
### Solution
Automate the process of extracting the relevant information from the reports and sending a daily summary email to the business owner.

## Workflow
1. Capture third party provider's daily reports sent to client via email (Zapier)
1. Store the reports (ActivePieces, AWS S3)
1. Parse the reports to extract the relevant information (Python, Raspberry Pi)
1. Send a daily summary email to the business owner (Sendgrid)

## Notes and Learnings
### Zapier and ActivePieces
Zapier and the *Go To* for automating workflows. However, it is on the pricier side. ActivePieces is an open-source alternative that can be used to automate workflows. I used ActivePieces for all the pieces that I could, but I had to use Zapier for the email handling because ActivePieces does not handle emails with multiple attachments very well. 

### PDFs
Most of the third-party reports are in PDF format -- which are not as simple to extract data from as plain text files. After first paying a service to parse the PDFs, I found multiple python libraries to do the trick. In the end, I found [pdftotext](https://pypi.org/project/pdftotext/) to be the best for my use case.

### Storing the Reports
While storing the reports is not necessary, I chose to do so because the reports contain valuable data that the business owner may want to access later. Additionally, this allowed my to make the workflow more modular and resilient to errors. It's great how cheap and easy to use AWS S3 is for this purpose.

### Regex and Copilots
I used regex to extract the relevant information from the reports once they were turned into strings. In doing so I found my new favorite use case for LLM copilots: Writing Regular Expressions!

### Production
The main challenge in production was handling the various edge cases that occurred when dealing with third-party vendors. For example, occasionally vendors will not send a report. I had to make sure that the system could handle these cases without crashing or causing the whole system to melt down.

## Recurring Costs
- Zapier: $30/month
- ActivePieces: Free Tier
- AWS S3: $0.023/GB
- Sendgrid: Free Tier

## Possible Extensions
- Create weekly and monthly reports
- Add trends or historical data to the reports
- Improve error handling and messaging
- Add charts and graphs to the report$s
- Host on a cloud server instead of a local server to make more resilient... my niece likes unplugging my raspberry pi
- Move Zapier functionality to ActivePieces to reduce costs
- Delete S3 files after processing to reduce storage costs
- Host ActivePieces locally to reduce costs