# READ ME
Before sending this code to AWS ensure you have met the following requirements
## S3 Bucket
OFA Lambda is too big, please create a bucket to house the package. Since OFA is on S3 please include all packages onto S3 so we can group them in one area.
## Lambda
We need 3 lambda's are minimum for Google Crawler, OFA Scraper, and SS Scraper. Please make one for each. It would be nice to have a 4th lambda that will launch all three for demo purposes.   
From here all you have to do is copy the path from S3 and place the link into the lambda (ensure you click upload from S3, THEN paste the link)
