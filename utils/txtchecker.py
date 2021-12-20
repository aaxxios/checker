from textcleanup import (
    split_into_chunks,
    calculate_unique_score_for_chunk,
    remove_special_characters,
)
from handlequeries import build_query_result


def get_queries(source, num_queries=3):
    scored_chunks = []

    for chunk in split_into_chunks(source, filter_poor_quality=True):
        score = calculate_unique_score_for_chunk(chunk)
        scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=source)

source = """What is a blog anyway?
In short, a blog is a type of website that focuses mainly on written content, also known as blog posts. In popular culture we most often hear about news blogs or celebrity blog sites, but as you’ll see in this guide, you can start a successful blog on just about any topic imaginable.
Bloggers often write from a personal perspective that allows them to connect directly with their readers. In addition, most blogs also have a “comments” section where visitors can correspond with the blogger. Interacting with your visitors in the comments section helps to further the connection between the blogger and the reader.
This direct connection to the reader is one of the main benefits of starting a blog. This connection allows you to interact and share ideas with other like-minded people. It also allows you to build trust with your readers. Having the trust and loyalty of your readers also opens up the door to making money from your blog, which is something I discuss later in this guide.
The good news is that the internet is exploding with growth right now. More people than ever are online. This explosion in growth means more potential readers for your blog. In short, if you are thinking about starting a blog then there is no better time than right now.
Let’s start your blog!

"""

print(get_queries(source))