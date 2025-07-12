from pathlib import Path

import scrapy

class QuotesSpider(scrapy.Spider):
    name = "git"

    async def start(self):
        repos = [
            "https://github.com/JacktheGeat/jackthegeat.github.io"
        ]
        for url in repos:
            yield scrapy.Request(url=url, callback=self.parse_repo)

    def parse_repo(self, response):
        page = response.url.split("/")[-1]
        filename = f"git-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
        yield {
            "title": response.css("title::text").get(),
            "creator": response.url.split("/")[-2],
            "number of stars": response.css("div.Layout-sidebar div div div div div.mt-2")[1].css("strong::text").get(),
            "number of watchers": response.css("div.Layout-sidebar div div div div div.mt-2")[2].css("strong::text").get(),
            "number of forks": response.css("div.Layout-sidebar div div div div div.mt-2")[3].css("strong::text").get(),
            "issues list": response.css('a[id="issues-tab"]::attr(href)').get(),
        }
        issuesPage = response.css('a[id="issues-tab"]::attr(href)').get()
        issuesPage = response.urljoin(issuesPage)
        yield scrapy.Request(issuesPage, callback=self.parse_issues)

    def parse_issues(self, response):
        page = response.url.split("/")[-2]
        filename = f"git-{page}-issues.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
        # open_issues = response.urljoin(response.url + "?q=is%3Aissue%20state%3Aopen")
        # closed_issues = response.urljoin(response.url + "?q=is%3Aissue%20state%3Aclosed")
        yield {
            "link": response.url,
            "num open issues": response.css('div[id=":rd:-list-view-metadata"]'),
            # "num closed issues": response.css("ul.list-style-none ListItems-module__tabsContainer--qrUH2")
        }