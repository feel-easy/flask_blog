import markdown
# from markdown.extensions.toc import TocExtension

str = ''
with open('../python time模块和datetime模块详解.md', 'r', encoding='utf-8') as f:
    str = f.read()

md = markdown.Markdown(extensions=[
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
    'markdown.extensions.toc',
    # TocExtension(slugify=''),
    # 'markdown.extensions.tables'

])
md_str = md.convert(str)
md_toc = md.toc
print(md_toc)
# md = markdown.Markdown(extensions=[
#             'markdown.extensions.extra',
#             'markdown.extensions.codehilite',
#             TocExtension(slugify=slugify),
#         ])
#         post.body = md.convert(post.body)
#         post.toc = md.toc

# with open('index.html', 'w', encoding='utf-8') as f:
#     f.write(md_str)
# print(md_str)
