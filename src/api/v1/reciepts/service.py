from datetime import datetime, timedelta
from sqlalchemy import case, distinct, func, desc, and_
from typing import Optional, List, Dict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from api.v1.users.model import User, Payment, PaymentItem, TransactionStatus, Department, Level, RoleEnum, Session, Organization
from utils.dependency import db
from api.v1.auth.service import AuthService
import logging

#setup logging
service_logger = logging.getLogger(__name__)
service_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/reciept.log')
file_handler.setFormatter(formatter)
service_logger.addHandler(file_handler)

class PaymentPeriod(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

@dataclass
class PaymentAnalytics:
    total_amount: Decimal
    count: int
    period: str
    breakdown: Dict

class ReceiptService:
    def __init__(self):
        self.db = db
        self.auth_service = AuthService(model=User)
    def generate_item_receipt(self, payment_reference: str) -> dict:
        """Generate receipt for a single payment item"""
        payment = self.db.session.query(Payment).filter_by(payment_reference=payment_reference).first()
        if not payment:
            raise ValueError("Payment not found")

        service_logger.info(f"Receipt generated for payment: {payment}")
        data =  {
            "receipt_no": f"RCP-{payment.id}",
            "date": payment.payment_date.strftime("%Y-%m-%d"),
            "student_info": {
                "name": payment.user.full_name,
                "organization": payment.user.organization.acronym,
                "matric_number": payment.user.matric_number,
                "department": payment.user.department.name,
                "level": payment.user.level.name,
                "faculty": payment.user.faculty,
                "campus": payment.user.campus
            },
            "payment_info": {
                "name": payment.payment_item.name,
                "amount": float(payment.amount),
                "status": payment.status,
                "reference": payment.payment_reference,
                "transaction_id": payment.transaction_id,
                "payment_method": payment.payment_method,
                "session": payment.payment_item.academic_session.name,
                "date": str(payment.updated_at),
            }
        }
        service_logger.info(f"Receipt data: {data}")
        return data
        str()
    def generate_session_receipt(self) -> dict:
        """Generate consolidated receipt for all payments in a session"""
        user = self.auth_service.get_current_user()
        user_id = user.id
        session_id = (
            db.session.query(Session.id)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(Organization.acronym == user.organization.acronym, Session.is_active == True)
            .scalar()
        )
        payments = self.db.session.query(Payment)\
            .join(PaymentItem)\
            .filter(
                Payment.user_id == user_id,
                PaymentItem.academic_session_id == session_id,
                Payment.status == TransactionStatus.PAID.value
            ).all()

        if not payments:
            raise ValueError("No payments found for this session")

        total_amount = sum(payment.amount for payment in payments)
        
        reciept_data =  {
            "receipt_no": f"SES-{session_id}-{user_id}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "student_info": {
                "name": payments[0].user.full_name,
                "organization": payments[0].user.organization.acronym,
                "matric_number": payments[0].user.matric_number,
                "department": payments[0].user.department.name,
                "level": payments[0].user.level.name,
                "faculty": payments[0].user.faculty,
                "campus": payments[0].user.campus
            },
            "session": payments[0].payment_item.academic_session.name,
            "items": [{
                "name": payment.payment_item.name,
                "amount": float(payment.amount),
                "date_paid": payment.payment_date.strftime("%Y-%m-%d"),
                "status": payment.status,
                "reference": payment.payment_reference
            } for payment in payments],
            "total_amount": float(total_amount)
        }
        service_logger.info(reciept_data)
        return reciept_data



class AnalyticsService:
    def __init__(self):
        self.db = db
        self.auth_service = AuthService(model=User)

    def _get_user_scope(self, user) -> dict:
        """Determine query filters based on user role"""
        filters = {}
        if user.role.name == RoleEnum.ADMIN or user.role.name == RoleEnum.BURSAR:
            filters['organization_id'] = user.organization_id
        elif user.role.name == RoleEnum.SUBADMIN:
            filters['organization_id'] = user.organization_id
            filters['department_id'] = user.department_id
        elif user.role.name == RoleEnum.STUDENT:
            filters['user_id'] = user.id
        return filters

    def get_payment_analytics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get payment analytics based on user role and date range"""
        user = self.auth_service.get_current_user()
        filters = self._get_user_scope(user)
        
        # Build date filter
        date_filter = and_(
            Payment.payment_date >= start_date if start_date else True,
            Payment.payment_date <= end_date if end_date else True
        )

        # Base query with corrected joins
        base_query = self.db.session.query(Payment)
        
        # Apply role-based filters with explicit joins
        if filters.get('organization_id'):
            base_query = base_query.join(
                PaymentItem, Payment.payment_item_id == PaymentItem.id
            ).filter(PaymentItem.organization_id == filters['organization_id'])
        if filters.get('department_id'):
            base_query = base_query.join(
                User, Payment.user_id == User.id
            ).filter(User.department_id == filters['department_id'])
        if filters.get('user_id'):
            base_query = base_query.filter(Payment.user_id == filters['user_id'])

        # Apply analytics aggregations
        query = base_query.with_entities(
            func.count(Payment.id).label('total_transactions'),
            func.sum(Payment.amount).label('total_amount'),
            func.avg(Payment.amount).label('average_payment'),
            func.count(case((Payment.status == 'Paid', 1))).label('successful_payments'),
            func.count(case((Payment.status == 'Failed', 1))).label('failed_payments'),
            func.min(Payment.amount).label('min_payment'),
            func.max(Payment.amount).label('max_payment'),
            func.count(case((Payment.status == 'Pending', 1))).label('pending_payments'),
            func.count(case((Payment.status == 'Refunded', 1))).label('refunded_payments')
        ).filter(date_filter)

        results = query.first()
        
        if not results:
            return {
                'total_transactions': 0,
                'total_amount': 0.0,
                'average_payment': 0.0,
                'successful_payments': 0,
                'failed_payments': 0,
                'success_rate': 0.0,
                'min_payment': 0.0,
                'max_payment': 0.0,
                'pending_payments': 0,
                'refunded_payments': 0
            }

        total_transactions = results[0] or 0
        total_amount = float(results[1] or 0)
        average_payment = float(results[2] or 0)
        successful_payments = results[3] or 0
        failed_payments = results[4] or 0
        min_payment = float(results[5] or 0)
        max_payment = float(results[6] or 0)
        pending_payments = results[7] or 0
        refunded_payments = results[8] or 0

        success_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0

        return {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'average_payment': average_payment,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'success_rate': round(success_rate, 2),
            'min_payment': min_payment,
            'max_payment': max_payment,
            'pending_payments': pending_payments,
            'refunded_payments': refunded_payments
        }


    def get_registration_analytics(self) -> Dict:
        user = self.auth_service.get_current_user()
        """Get registration analytics based on user role"""
        filters = self._get_user_scope(user)
        
        query = self.db.session.query(User)
        
        if filters.get('organization_id'):
            query = query.filter(User.organization_id == filters['organization_id'])
        if filters.get('department_id'):
            query = query.filter(User.department_id == filters['department_id'])
        if filters.get('user_id'):
            query = query.filter(User.id == filters['user_id'])

        total_users = query.count()
        users_by_level = query.with_entities(
            Level.name, func.count(User.id)
        ).join(Level).group_by(Level.name).all()
        
        users_by_department = None
        if user.role.name in [RoleEnum.ADMIN, RoleEnum.BURSAR, "SUPERADMIN"]:
            users_by_department = query.with_entities(
                Department.name, func.count(User.id)
            ).join(Department).group_by(Department.name).all()

        return {
            'total_users': total_users,
            'users_by_level': dict(users_by_level),
            'users_by_department': dict(users_by_department) if users_by_department else None
        }

    def get_payment_trends(self, days: int = 30) -> List[Dict]:
        """Get payment trends over time"""
        user = self.auth_service.get_current_user()
        filters = self._get_user_scope(user)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.session.query(
            func.date(Payment.payment_date).label('date'),
            func.sum(Payment.amount).label('daily_total'),
            func.count(Payment.id).label('daily_count')
        ).filter(Payment.payment_date.between(start_date, end_date))

        if filters.get('organization_id'):
            query = query.join(PaymentItem).filter(
                PaymentItem.organization_id == filters['organization_id']
            )
        if filters.get('department_id'):
            query = query.join(User).filter(
                User.department_id == filters['department_id']
            )
        if filters.get('user_id'):
            query = query.filter(Payment.user_id == filters['user_id'])

        return [
            {
                'date': row.date.strftime('%Y-%m-%d'),
                'total_amount': float(row.daily_total or 0),
                'transaction_count': row.daily_count
            }
            for row in query.group_by(func.date(Payment.payment_date))
            .order_by(func.date(Payment.payment_date)).all()
        ]

    def get_popular_payment_items(self, limit: int = 10) -> List[Dict]:
        """Get most popular payment items"""
        user = self.auth_service.get_current_user()
        filters = self._get_user_scope(user)
        
        query = self.db.session.query(
            PaymentItem.name,
            func.count(Payment.id).label('payment_count'),
            func.sum(Payment.amount).label('total_amount')
        ).join(Payment)

        if filters.get('organization_id'):
            query = query.filter(PaymentItem.organization_id == filters['organization_id'])
        if filters.get('department_id'):
            query = query.filter(PaymentItem.department_id == filters['department_id'])
        if filters.get('user_id'):
            query = query.filter(Payment.user_id == filters['user_id'])

        return [
            {
                'name': row.name,
                'payment_count': row.payment_count,
                'total_amount': float(row.total_amount or 0)
            }
            for row in query.group_by(PaymentItem.name)
            .order_by(desc('payment_count')).limit(limit).all()
        ]

    def get_department_performance(self) -> List[Dict]:
        """Get department performance metrics (only for ADMIN and above)"""
        user = self.auth_service.get_current_user()
        if user.role.name not in [RoleEnum.ADMIN, RoleEnum.BURSAR, "SUPERADMIN"]:
            return []

        filters = self._get_user_scope(user)
        
        query = self.db.session.query(
            Department.name,
            func.count(distinct(User.id)).label('student_count'),
            func.count(Payment.id).label('payment_count'),
            func.sum(Payment.amount).label('total_amount'),
            func.avg(Payment.amount).label('average_payment')
        ).join(User, Department.id == User.department_id)\
         .outerjoin(Payment, User.id == Payment.user_id)

        if filters.get('organization_id'):
            query = query.filter(Department.organization_id == filters['organization_id'])

        return [
            {
                'department': row.name,
                'student_count': row.student_count,
                'payment_count': row.payment_count,
                'total_amount': float(row.total_amount or 0),
                'average_payment': float(row.average_payment or 0)
            }
            for row in query.group_by(Department.name).all()
        ]

    def get_session_analytics(self, session_id: Optional[int] = None) -> Dict:
        """Get analytics for specific academic session"""
        user = self.auth_service.get_current_user()
        filters = self._get_user_scope(user)
        
        query = self.db.session.query(
            Session.name,
            func.count(distinct(User.id)).label('total_students'),
            func.count(Payment.id).label('total_payments'),
            func.sum(Payment.amount).label('total_amount')
        ).join(Level)\
         .join(User)\
         .outerjoin(Payment)

        if session_id:
            query = query.filter(Session.id == session_id)
        if filters.get('organization_id'):
            query = query.filter(Session.organization_id == filters['organization_id'])
        if filters.get('department_id'):
            query = query.filter(User.department_id == filters['department_id'])
        if filters.get('user_id'):
            query = query.filter(User.id == filters['user_id'])

        result = query.group_by(Session.name).first()
        
        if not result:
            return {}

        return {
            'session_name': result.name,
            'total_students': result.total_students,
            'total_payments': result.total_payments,
            'total_amount': float(result.total_amount or 0),
            'average_payment_per_student': float(result.total_amount / result.total_students if result.total_students else 0)
        }
receipt_service = ReceiptService()
analytics_service = AnalyticsService()