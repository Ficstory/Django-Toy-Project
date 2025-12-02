from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from openai import OpenAI
from .models import StockData
from django.http import HttpResponse

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import UserInterestStock
from .models import StockComment
from contentfetch.crawler import fetch_toss_comments
from typing import List, Dict
from django.db import transaction

# ---- OpenAI Client ----
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def ask_comment(prompt, model="gpt-5-nano"):
    """OpenAI 모델을 사용해 댓글 분석"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"오류 발생: {e}"

def analyze_comments(comments, company_name):
    """댓글을 GPT 모델로 분석"""
    if comments:
        combined_comments = "\n".join(comments)
        prompt = f"다음은 {company_name}에 대한 댓글들입니다. 종합적인 분석을 한글로 작성하고, 마지막 줄에는 여론을 긍정적, 부정적, 중립으로 판단해 주세요:\n{combined_comments}"
        return ask_comment(prompt)
    return "댓글을 찾을 수 없습니다."


def stock_finder(request):
    if request.method == "POST":
        company_name = request.POST.get('company_name', '').strip()
        if company_name:
            # 종목 검색 후 바로 상세 페이지로 리디렉션
            return redirect('contentfetch:stock_detail', stock_name=company_name)
        else:
            # 입력이 없는 경우, 에러 메시지와 함께 폼을 다시 표시
            return render(request, 'contentfetch/stock_finder.html', {'error_message': "회사 이름을 입력하세요."})
    
    # GET 요청 시, 그냥 검색 폼을 표시
    return render(request, 'contentfetch/stock_finder.html')


@require_POST
@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(StockComment, pk=pk)
    stock_name = comment.stock_name
    comment.delete()
    return redirect('contentfetch:stock_detail', stock_name=stock_name)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()        # 사용자 생성
            login(request, user)      # 자동 로그인
            return redirect('contentfetch:stock_finder')  # 메인으로 이동
    else:
        form = UserCreationForm()
    return render(request, 'contentfetch/signup.html', {'form': form})


@login_required
def profile(request):
    stocks = request.user.interest_stocks.order_by('-created_at')
    return render(request, 'contentfetch/profile.html', {'stocks': stocks})

@require_POST
@login_required
def add_interest(request):
    name = request.POST.get('stock_name', '').strip()
    if name:
        UserInterestStock.objects.get_or_create(user=request.user, stock_name=name)
    return redirect('contentfetch:profile')

@login_required
def delete_interest(request, pk):
    obj = get_object_or_404(UserInterestStock, pk=pk, user=request.user)
    obj.delete()
    return redirect('contentfetch:profile')

def stock_detail(request, stock_name): return HttpResponse(f"detail {stock_name} stub")


def ensure_comments(stock_name: str):
    # 1) DB에 이미 있으면 그대로 사용
    qs = StockComment.objects.filter(stock_name=stock_name).order_by("-crawled_at")
    if qs.exists():
        print("[ENSURE] hit DB:", qs.count())
        return list(qs.values("pk", "comment"))

    # 2) 없으면 크롤러 호출 → 정규화 → DB 저장
    from contentfetch.crawler import fetch_toss_comments
    data = fetch_toss_comments(stock_name, limit=50)
    items = data.get("comments", []) if isinstance(data, dict) else (data or [])

    norm = []
    for it in items:
        txt = (it.get("comment") or it.get("text") or "").strip() if isinstance(it, dict) else str(it).strip()
        if txt:
            norm.append(txt)

    to_create = [StockComment(stock_name=stock_name, comment=txt, source="Toss") for txt in norm]
    if to_create:
        with transaction.atomic():
            StockComment.objects.bulk_create(to_create)
        print("[ENSURE] saved to DB:", len(to_create))

    # 3) 저장 후 다시 DB에서 읽어 반환
    return list(
        StockComment.objects.filter(stock_name=stock_name)
        .order_by("-crawled_at")
        .values("pk", "comment")
    )


# def stock_detail(request, stock_name):
#     comments = ensure_comments(stock_name)
#     return render(
#         request,
#         'contentfetch/stock_detail.html',
#         {'stock_name': stock_name, 'comments': comments}
#     )

def stock_detail(request, stock_name):
    print("[DETAIL] calling ensure_comments:", stock_name)
    comments = ensure_comments(stock_name)   # ← 반드시 이 함수를 호출해야 DB 저장/재사용 흐름이 동작
    print("[DETAIL] got comments:", len(comments))
    return render(
        request,
        "contentfetch/stock_detail.html",
        {"stock_name": stock_name, "comments": comments, "error": None},
    )

def _fetch_comments_only(stock_name: str):
    # DB는 건너뛰고, 크롤러 결과만 화면에 뿌리기
    from contentfetch.crawler import fetch_toss_comments
    data = fetch_toss_comments(stock_name, limit=5)
    items = data.get("comments", []) if isinstance(data, dict) else (data or [])
    return [
        {"comment": (it.get("comment") or it.get("text") or "").strip()}
        for it in items
        if (it.get("comment") or it.get("text"))
    ]