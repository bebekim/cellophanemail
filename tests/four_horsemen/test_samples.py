"""Multilingual test samples for Four Horsemen analysis - English and Korean."""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ToxicityLevel(Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    HARMFUL = "HARMFUL"
    ABUSIVE = "ABUSIVE"


class FourHorseman(Enum):
    CRITICISM = "criticism"
    CONTEMPT = "contempt"
    DEFENSIVENESS = "defensiveness"
    STONEWALLING = "stonewalling"


@dataclass
class EmailTestSample:
    """Test sample with ground truth labels."""
    id: str
    language: str  # "en" or "ko"
    sender: str
    subject: str
    content: str
    expected_classification: ToxicityLevel
    expected_horsemen: List[FourHorseman]
    category: str
    description: str


# English Test Samples
ENGLISH_SAMPLES = [
    # SAFE - Business Communication
    EmailTestSample(
        id="en_safe_001",
        language="en",
        sender="notifications@company.com",
        subject="Weekly Team Update",
        content="""Hi team,

I hope everyone is doing well. Here's our weekly update:

- Project Alpha is on track for next week's deadline
- The client meeting went successfully on Tuesday
- Please review the attached documents by Friday

Let me know if you have any questions.

Best regards,
Sarah""",
        expected_classification=ToxicityLevel.SAFE,
        expected_horsemen=[],
        category="business_communication",
        description="Professional team update email"
    ),

    EmailTestSample(
        id="en_safe_002", 
        language="en",
        sender="support@service.com",
        subject="Your Order Confirmation #12345",
        content="""Thank you for your order!

Your order #12345 has been confirmed and will be shipped within 2-3 business days.

Items ordered:
- Widget A (Qty: 2)
- Widget B (Qty: 1)

Tracking information will be sent to your email once shipped.

Thank you for choosing our service!""",
        expected_classification=ToxicityLevel.SAFE,
        expected_horsemen=[],
        category="business_communication",
        description="Order confirmation email"
    ),

    # WARNING - Mild tension
    EmailTestSample(
        id="en_warning_001",
        language="en", 
        sender="manager@company.com",
        subject="Re: Project Delay",
        content="""Hi John,

I'm concerned about the project delay. This is the second time this month we've had timing issues.

Could you please explain what happened and how we can prevent this going forward?

We need to discuss this in our 1-on-1 tomorrow.

Thanks,
Mike""",
        expected_classification=ToxicityLevel.WARNING,
        expected_horsemen=[],
        category="workplace_tension",
        description="Manager expressing concern about performance"
    ),

    # HARMFUL - Criticism
    EmailTestSample(
        id="en_harmful_001",
        language="en",
        sender="colleague@company.com",
        subject="Re: Your Presentation",
        content="""You always mess up these presentations. You never prepare properly and it shows.

You're so disorganized and it's embarrassing for the whole team. 

You can't seem to get anything right lately.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.CRITICISM],
        category="workplace_toxicity",
        description="Personal attack with 'always/never' criticism"
    ),

    # ABUSIVE - Contempt + Criticism
    EmailTestSample(
        id="en_abusive_001",
        language="en",
        sender="toxic@company.com", 
        subject="You're pathetic",
        content="""You're absolutely pathetic. I can't believe they hired someone so incompetent.

You're a complete waste of space and everyone knows it. You'll never amount to anything.

I'm so much better than you and everyone can see it.""",
        expected_classification=ToxicityLevel.ABUSIVE,
        expected_horsemen=[FourHorseman.CONTEMPT, FourHorseman.CRITICISM],
        category="workplace_toxicity", 
        description="Extreme contempt with character assassination"
    ),

    # HARMFUL - Defensiveness
    EmailTestSample(
        id="en_harmful_002",
        language="en",
        sender="defensive@company.com",
        subject="Re: Missing Deadline",
        content="""It's not my fault the deadline was missed. You gave me impossible requirements.

If you hadn't changed the specs three times, this wouldn't have happened. 

You made me work with inadequate resources. This is all on you, not me.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.DEFENSIVENESS],
        category="workplace_conflict",
        description="Deflecting blame and counter-attacking"
    ),

    # HARMFUL - Stonewalling  
    EmailTestSample(
        id="en_harmful_003",
        language="en",
        sender="silent@company.com",
        subject="Re: Team Meeting",
        content="""Whatever. I'm done talking about this.

I'm not discussing this anymore. Find someone else to deal with your problems.

Talk to the hand.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.STONEWALLING],
        category="workplace_conflict",
        description="Emotional withdrawal and communication shutdown"
    ),
]


# Korean Test Samples  
KOREAN_SAMPLES = [
    # SAFE - Business Communication
    EmailTestSample(
        id="ko_safe_001",
        language="ko",
        sender="알림@회사.com",
        subject="주간 팀 업데이트",
        content="""팀 여러분 안녕하세요,

모두 잘 지내고 계시길 바랍니다. 이번 주 업데이트입니다:

- 프로젝트 알파는 다음 주 마감일에 맞춰 순조롭게 진행되고 있습니다
- 화요일 고객 미팅이 성공적으로 진행되었습니다  
- 첨부된 문서를 금요일까지 검토해 주세요

궁금한 점이 있으시면 언제든 말씀해 주세요.

감사합니다,
김사라""",
        expected_classification=ToxicityLevel.SAFE,
        expected_horsemen=[],
        category="business_communication",
        description="Professional team update in Korean"
    ),

    EmailTestSample(
        id="ko_safe_002",
        language="ko", 
        sender="고객지원@서비스.com",
        subject="주문 확인 #12345",
        content="""주문해 주셔서 감사합니다!

주문번호 #12345가 확인되었으며 2-3일 내에 발송될 예정입니다.

주문 상품:
- 위젯 A (수량: 2)
- 위젯 B (수량: 1)  

배송 정보는 발송 후 이메일로 안내드리겠습니다.

저희 서비스를 이용해 주셔서 감사합니다!""",
        expected_classification=ToxicityLevel.SAFE,
        expected_horsemen=[],
        category="business_communication", 
        description="Order confirmation in Korean"
    ),

    # WARNING - Mild concern
    EmailTestSample(
        id="ko_warning_001",
        language="ko",
        sender="매니저@회사.com", 
        subject="프로젝트 지연 관련",
        content="""안녕하세요 김대리님,

프로젝트 지연에 대해 우려가 있습니다. 이번 달에만 벌써 두 번째 일정 문제입니다.

무슨 일이 있었는지, 앞으로 어떻게 예방할 수 있는지 설명해 주실 수 있나요?

내일 1:1 미팅에서 이 문제를 논의해야겠습니다.

감사합니다,
박부장""",
        expected_classification=ToxicityLevel.WARNING,
        expected_horsemen=[],
        category="workplace_tension",
        description="Manager expressing concern in Korean"
    ),

    # HARMFUL - Criticism (Korean patterns)
    EmailTestSample(
        id="ko_harmful_001", 
        language="ko",
        sender="동료@회사.com",
        subject="당신의 발표에 대해",
        content="""당신은 항상 발표를 망쳐놓습니다. 준비를 제대로 하지 않아서 티가 다 납니다.

정말 무능하고 팀 전체가 창피합니다.

당신은 아무것도 제대로 못하는군요.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.CRITICISM],
        category="workplace_toxicity",
        description="Personal attack with Korean criticism patterns"
    ),

    # ABUSIVE - Contempt (Korean insults)
    EmailTestSample(
        id="ko_abusive_001",
        language="ko",
        sender="독성@회사.com",
        subject="정말 한심하다",
        content="""정말 한심합니다. 이렇게 무능한 사람을 어떻게 뽑았는지 모르겠어요.

당신은 완전히 쓸모없는 존재고 모든 사람이 다 알고 있어요.

나는 당신보다 훨씬 뛰어나고 모든 사람이 볼 수 있습니다.""",
        expected_classification=ToxicityLevel.ABUSIVE,
        expected_horsemen=[FourHorseman.CONTEMPT, FourHorseman.CRITICISM],
        category="workplace_toxicity",
        description="Extreme contempt with Korean insults"
    ),

    # HARMFUL - Defensiveness (Korean patterns)
    EmailTestSample(
        id="ko_harmful_002",
        language="ko",
        sender="변명@회사.com", 
        subject="마감일 관련",
        content="""마감일을 놓친 것은 내 잘못이 아닙니다. 불가능한 요구사항을 주셨잖아요.

사양을 세 번이나 바꾸지 않았다면 이런 일은 없었을 겁니다.

부족한 자원으로 일하게 만든 건 당신입니다. 이건 다 당신 책임이지 내 잘못이 아닙니다.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.DEFENSIVENESS],
        category="workplace_conflict", 
        description="Deflecting blame in Korean"
    ),

    # HARMFUL - Stonewalling (Korean patterns)
    EmailTestSample(
        id="ko_harmful_003",
        language="ko",
        sender="침묵@회사.com",
        subject="팀 미팅 관련",
        content="""그냥 됐습니다. 더 이상 이야기하고 싶지 않아요.

이것에 대해서는 더 이상 논의하지 않겠습니다. 다른 사람 찾아서 해결하세요.

무시할 겁니다.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.STONEWALLING],
        category="workplace_conflict",
        description="Communication shutdown in Korean"
    ),

    # Mixed Language Sample
    EmailTestSample(
        id="mixed_harmful_001",
        language="mixed",
        sender="bilingual@company.com",
        subject="Re: Project Issues 프로젝트 문제",
        content="""You always mess up everything. 당신은 정말 무능해요.

This is so frustrating. 이런 식으로 계속하면 안 됩니다.

I can't work with someone like you. 당신같은 사람과는 일할 수 없어요.""",
        expected_classification=ToxicityLevel.HARMFUL,
        expected_horsemen=[FourHorseman.CRITICISM, FourHorseman.CONTEMPT],
        category="workplace_toxicity",
        description="Code-switching toxic communication"
    ),
]


# Combined samples
ALL_SAMPLES = ENGLISH_SAMPLES + KOREAN_SAMPLES


def get_samples_by_classification(classification: ToxicityLevel) -> List[EmailTestSample]:
    """Get samples by toxicity classification."""
    return [sample for sample in ALL_SAMPLES if sample.expected_classification == classification]


def get_samples_by_language(language: str) -> List[EmailTestSample]:
    """Get samples by language."""
    return [sample for sample in ALL_SAMPLES if sample.language == language]


def get_samples_by_horseman(horseman: FourHorseman) -> List[EmailTestSample]:
    """Get samples containing specific Four Horseman pattern."""
    return [sample for sample in ALL_SAMPLES if horseman in sample.expected_horsemen]


def get_samples_by_category(category: str) -> List[EmailTestSample]:
    """Get samples by category.""" 
    return [sample for sample in ALL_SAMPLES if sample.category == category]


def get_test_sample_summary() -> Dict[str, Any]:
    """Get summary statistics of test samples."""
    total_samples = len(ALL_SAMPLES)
    english_samples = len([s for s in ALL_SAMPLES if s.language == "en"])
    korean_samples = len([s for s in ALL_SAMPLES if s.language == "ko"])
    mixed_samples = len([s for s in ALL_SAMPLES if s.language == "mixed"])
    
    by_classification = {}
    for classification in ToxicityLevel:
        by_classification[classification.value] = len(get_samples_by_classification(classification))
    
    by_horseman = {}
    for horseman in FourHorseman:
        by_horseman[horseman.value] = len(get_samples_by_horseman(horseman))
    
    return {
        "total_samples": total_samples,
        "by_language": {
            "english": english_samples,
            "korean": korean_samples, 
            "mixed": mixed_samples
        },
        "by_classification": by_classification,
        "by_horseman": by_horseman,
        "categories": list(set(sample.category for sample in ALL_SAMPLES))
    }


# Export for easy import
__all__ = [
    "EmailTestSample", 
    "ToxicityLevel", 
    "FourHorseman",
    "ALL_SAMPLES", 
    "ENGLISH_SAMPLES", 
    "KOREAN_SAMPLES",
    "get_samples_by_classification",
    "get_samples_by_language", 
    "get_samples_by_horseman",
    "get_samples_by_category",
    "get_test_sample_summary"
]