"""Tests for JWT token service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import jwt
from cellophanemail.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    TokenType,
    TokenPayload,
    JWTError
)


class TestJWTTokenGeneration:
    """Test JWT token generation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_access_token_with_valid_user_data(self):
        """Test creating an access token with valid user data."""
        # Given
        user_id = "user_123"
        email = "test@example.com"
        role = "user"
        
        # When
        token = create_access_token(
            user_id=user_id,
            email=email,
            role=role
        )
        
        # Then
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Verify token can be decoded
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        assert decoded["sub"] == user_id
        assert decoded["email"] == email
        assert decoded["role"] == role
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded  # JWT ID for blacklisting
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self):
        """Test creating a refresh token."""
        # Given
        user_id = "user_123"
        
        # When
        token = create_refresh_token(user_id=user_id)
        
        # Then
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token content
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        assert decoded["sub"] == user_id
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
        assert "jti" in decoded
    
    @pytest.mark.asyncio
    async def test_access_token_expires_in_15_minutes(self):
        """Test that access tokens expire in 15 minutes."""
        # Given
        user_id = "user_123"
        
        # When
        with patch('cellophanemail.services.jwt_service.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            token = create_access_token(user_id=user_id, email="test@example.com")
        
        # Then
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        expected_exp = mock_now + timedelta(minutes=15)
        
        assert abs((exp_datetime - expected_exp).total_seconds()) < 2
    
    @pytest.mark.asyncio
    async def test_refresh_token_expires_in_7_days(self):
        """Test that refresh tokens expire in 7 days."""
        # Given
        user_id = "user_123"
        
        # When
        with patch('cellophanemail.services.jwt_service.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            token = create_refresh_token(user_id=user_id)
        
        # Then
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        expected_exp = mock_now + timedelta(days=7)
        
        assert abs((exp_datetime - expected_exp).total_seconds()) < 2


class TestJWTTokenVerification:
    """Test JWT token verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self):
        """Test verifying a valid token."""
        # Given
        token = create_access_token(
            user_id="user_123",
            email="test@example.com",
            role="user"
        )
        
        # When
        payload = await verify_token(token, TokenType.ACCESS)
        
        # Then
        assert payload is not None
        assert payload.sub == "user_123"
        assert payload.email == "test@example.com"
        assert payload.role == "user"
        assert payload.type == "access"
    
    @pytest.mark.asyncio
    async def test_verify_expired_token_raises_error(self):
        """Test that expired tokens raise an error."""
        # Given - Create an expired token
        with patch('cellophanemail.services.jwt_service.datetime') as mock_datetime:
            # Set time to past for token creation
            past_time = datetime.now(timezone.utc) - timedelta(hours=1)
            mock_datetime.now.return_value = past_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            token = create_access_token(
                user_id="user_123",
                email="test@example.com"
            )
        
        # When/Then - Verification should fail
        with pytest.raises(JWTError) as exc:
            await verify_token(token, TokenType.ACCESS)
        
        assert "expired" in str(exc.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_invalid_signature_raises_error(self):
        """Test that tokens with invalid signatures raise an error."""
        # Given - Tamper with token
        token = create_access_token(
            user_id="user_123",
            email="test@example.com"
        )
        # Modify last character
        tampered_token = token[:-1] + ('A' if token[-1] != 'A' else 'B')
        
        # When/Then
        try:
            result = await verify_token(tampered_token, TokenType.ACCESS)
            # If we get here, the test should fail because no exception was raised
            assert False, f"Expected JWTError but got result: {result}"
        except JWTError as e:
            # This is expected
            assert "invalid" in str(e).lower() or "signature" in str(e).lower()
        except Exception as e:
            # Unexpected exception type
            assert False, f"Expected JWTError but got {type(e).__name__}: {e}"
    
    @pytest.mark.asyncio
    async def test_verify_wrong_token_type_raises_error(self):
        """Test that using wrong token type raises an error."""
        # Given - Create refresh token but verify as access token
        token = create_refresh_token(user_id="user_123")
        
        # When/Then
        with pytest.raises(JWTError) as exc:
            await verify_token(token, TokenType.ACCESS)
        
        assert "Invalid token type" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_verify_blacklisted_token_raises_error(self):
        """Test that blacklisted tokens are rejected."""
        # Given
        token = create_access_token(
            user_id="user_123",
            email="test@example.com"
        )
        
        # Blacklist the token
        decoded = jwt.decode(token, options={"verify_signature": False})
        jti = decoded["jti"]
        
        with patch('cellophanemail.services.jwt_service.is_token_blacklisted') as mock_blacklist:
            mock_blacklist.return_value = True
            
            # When/Then
            with pytest.raises(JWTError) as exc:
                await verify_token(token, TokenType.ACCESS)
            
            assert "blacklisted" in str(exc.value).lower()
            mock_blacklist.assert_called_once_with(jti)


class TestJWTRefreshFlow:
    """Test JWT refresh token flow."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_generates_new_access_token(self):
        """Test that refresh token can generate new access token."""
        # Given
        user_id = "user_123"
        refresh_token = create_refresh_token(user_id=user_id)
        
        # When
        from cellophanemail.services.jwt_service import refresh_access_token
        new_access_token = await refresh_access_token(refresh_token)
        
        # Then
        assert new_access_token is not None
        payload = await verify_token(new_access_token, TokenType.ACCESS)
        assert payload.sub == user_id
        assert payload.type == "access"
    
    @pytest.mark.asyncio
    async def test_cannot_use_access_token_for_refresh(self):
        """Test that access tokens cannot be used for refresh."""
        # Given
        access_token = create_access_token(
            user_id="user_123",
            email="test@example.com"
        )
        
        # When/Then
        from cellophanemail.services.jwt_service import refresh_access_token
        with pytest.raises(JWTError) as exc:
            await refresh_access_token(access_token)
        
        assert "Invalid token type" in str(exc.value)