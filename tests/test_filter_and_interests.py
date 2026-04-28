from literature_digest.config import DEFAULT_CONFIG
from literature_digest.email_filter import classify_email
from literature_digest.interests import analyze_research_interests
from literature_digest.llm.offline_stub import OfflineStubClient
from literature_digest.models import EmailMessage


def test_promotional_email_is_skipped():
    email = EmailMessage(
        id="promo",
        thread_id="t",
        subject="Limited time discount offer",
        sender="promo@example.com",
        date=None,
        text="Sale coupon. Buy now. Unsubscribe.",
    )

    decision = classify_email(email, DEFAULT_CONFIG)

    assert decision.skip is True
    assert "promotional" in decision.reason or "marketing" in decision.reason


def test_academic_email_with_unsubscribe_is_not_skipped():
    email = EmailMessage(
        id="academic",
        thread_id="t",
        subject="Journal table of contents",
        sender="alerts@journal.example",
        date=None,
        text="New article DOI 10.1234/example. Unsubscribe.",
    )

    decision = classify_email(email, DEFAULT_CONFIG)

    assert decision.skip is False


def test_research_interests_are_structured_by_llm():
    profile = analyze_research_interests(
        "我关注五边形 COF 纳米管热导率和机器学习势函数。",
        OfflineStubClient(),
    )

    assert "五边形 COF" in profile.material_systems
    assert profile.high_priority_topics

