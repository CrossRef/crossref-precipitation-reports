## Notes

-- last-status-check
-- primary-name
-- counts-type
-- coverage_type
-- counts


# current 
https://api.crossref.org/members/98/works?filter=from-pub-date:2020-01-01,until-pub-date:2022-02-19,type:journal-article&rows=0

# current + future
https://api.crossref.org/members/98/works?filter=from-pub-date:2020-01-01,type:journal-article&rows=0

# backfile
https://api.crossref.org/members/98/works?filter=until-pub-date:2019-12-31,type:journal-article&rows=0
# all
https://api.crossref.org/members/98/works?filter=type:journal-article&rows=0

66705
259791
259747


326496
326452
326452

https://doi.crossref.org/getPrefixPublisher?prefix=10.1002



if content_type empty
  set selection to the most common content type
else
  set selection to last thing selected
