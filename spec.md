1. We are going to create a web scapper that collects and grabs data from different sites.
2. For each different site there will be different method and workflow to get data. 
3. We want to use a provider model, where we can plug in different providers for each webscrapping
4. Lets define the scrapping process
5. Web scrapping process
    a. Init - > Go to web site url and scan
    b. Figure out what data is on that page
    c. For each available data scrap and grap the data
    d. If there are more pages to go in og into those pages
    
    The above is and example workflow. We need to able to be define the workflow in json. each step of work flow can be command
    I will let you decide what is best
6. There might be post processing process 
7. There needs to be mulitple ways of being able to store data via provider. eg csv, postgres, sql server, mongo etc
8. Based on a workflow json file the system will grab data
 
