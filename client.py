from __future__ import print_function

import logging

import grpc
import api_pb2
import api_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = api_pb2_grpc.ScraperStub(channel)
        response = stub.Scrape(api_pb2.ScrapeRequest(urls=[
            'https://www.youtube.com/watch?v=QH2-TGUlwu4',
            'https://www.youtube.com/watch?v=QH2-TGUlwu4'
        ]))
    for url in response.scraped_urls:
        print(url.rtsp_url)


if __name__ == '__main__':
    logging.basicConfig()
    run()
