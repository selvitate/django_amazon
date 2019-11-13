from django.shortcuts import render, redirect
from django.conf import settings
from scrapyd_api import ScrapydAPI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
# from amazon_search_result_scrapper.amazon_2.launch import Launch
import sys
import time

scrapyd = ScrapydAPI('http://localhost:6800')


@csrf_exempt
@require_http_methods(['POST', 'GET'])
def crawl(request):
    if request.method == 'POST':
        scrapper_type = request.POST.get('scrapper_type', None)
        if scrapper_type == 'search_result':
            keywords = request.POST.get('keywords', None)
            max_pages = request.POST.get('max_pages', '1')
            if not keywords:
                return JsonResponse({'error': 'Missing  keywords in search_result scrapper'})
            request.session['task'] = scrapyd.schedule('default', 'amazon_search_result', keywords=keywords,
                                                       max_pages=max_pages)

        elif scrapper_type == 'page_scrapper':
            keyword = request.POST.get('keyword', None)
            with_rewiews = True if request.POST.get('with_rewiews', None) == 'on' else False
            image_manage = 'download' if request.POST.get('image_manage', None) == 'on' else 'link'
            request.session['task'] = scrapyd.schedule('default', 'amazon_product_page', keyword=keyword,
                                                       with_rewiews=with_rewiews,
                                                       image_manage=image_manage)
        return render(request, 'scrapy_api/index.html')
    elif request.method == 'GET':
        task_id = request.GET.get('task_id', None)
        status = scrapyd.job_status('default', task_id)
        if status == 'finished':
            try:
                return JsonResponse({'finished': True})
            except Exception as e:
                return JsonResponse({'error': str(e)})
        return render(request, 'scrapy_api/index.html')


def cancel(request):
    task_id = request.session['task']
    scrapyd.cancel('default', task_id)
    return redirect('crawl_url')
