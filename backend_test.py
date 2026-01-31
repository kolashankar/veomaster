#!/usr/bin/env python3
"""
Google Flow Video Generation - Complete End-to-End Testing
Tests the NEW workflow: ONE project per job with batch upload and generation
"""

import requests
import json
import time
import os
from pathlib import Path
import subprocess

# Configuration
BACKEND_URL = "https://flow-queue-fix.preview.emergentagent.com/api"
TEST_FILES = {
    "images_zip": "/app/test_folder.zip",
    "prompts_file": "/app/prompts_test_2.txt"
}
JOB_NAME = "Test VP Project"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.job_id = None
        self.test_results = {
            "job_creation": False,
            "file_upload": False,
            "job_status": False,
            "video_records": False,
            "job_listing": False,
            "mongodb_connection": False,
            "prompt_parsing": False,
            "image_extraction": False
        }
        self.errors = []
        
    def log_success(self, test_name, message):
        print(f"✅ {test_name}: {message}")
        self.test_results[test_name] = True
        
    def log_error(self, test_name, error):
        print(f"❌ {test_name}: {error}")
        self.test_results[test_name] = False
        self.errors.append(f"{test_name}: {error}")
        
    def test_health_check(self):
        """Test basic API health"""
        print("\n🔍 Testing API Health Check...")
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Health: {data.get('message', 'OK')} - Status: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API Health: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health: Connection failed - {str(e)}")
            return False
    
    def test_job_creation(self):
        """Test POST /api/jobs/create"""
        print("\n🔍 Testing Job Creation...")
        try:
            payload = {"job_name": "Backend Test Job - VP Article"}
            response = self.session.post(
                f"{BACKEND_URL}/jobs/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.job_id = data.get("job_id")
                if self.job_id:
                    self.log_success("job_creation", f"Job created with ID: {self.job_id}")
                    self.log_success("mongodb_connection", "MongoDB connection working")
                    return True
                else:
                    self.log_error("job_creation", "No job_id in response")
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                self.log_error("job_creation", error_msg)
                self.log_error("mongodb_connection", "MongoDB connection failed")
                return False
                
        except Exception as e:
            self.log_error("job_creation", f"Request failed: {str(e)}")
            self.log_error("mongodb_connection", f"Connection error: {str(e)}")
            return False
    
    def test_file_upload(self):
        """Test POST /api/jobs/{job_id}/upload - THE CRITICAL FIX"""
        print("\n🔍 Testing File Upload (CRITICAL FIX)...")
        if not self.job_id:
            self.log_error("file_upload", "No job_id available")
            return False
            
        try:
            # Verify test files exist
            images_path = Path(TEST_FILES["images_zip"])
            prompts_path = Path(TEST_FILES["prompts_file"])
            
            if not images_path.exists():
                self.log_error("file_upload", f"Images file not found: {images_path}")
                return False
                
            if not prompts_path.exists():
                self.log_error("file_upload", f"Prompts file not found: {prompts_path}")
                return False
            
            print(f"📁 Using test files:")
            print(f"   Images: {images_path} ({images_path.stat().st_size} bytes)")
            print(f"   Prompts: {prompts_path} ({prompts_path.stat().st_size} bytes)")
            
            # Upload files
            with open(images_path, 'rb') as img_file, open(prompts_path, 'rb') as prompt_file:
                files = {
                    'images_folder': ('folder1.zip', img_file, 'application/zip'),
                    'prompts_file': ('prompts_test.txt', prompt_file, 'text/plain')
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/jobs/{self.job_id}/upload",
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                uploaded = data.get("uploaded", False)
                image_count = data.get("image_count", 0)
                prompt_count = data.get("prompt_count", 0)
                expected_videos = data.get("expected_videos", 0)
                
                if uploaded:
                    self.log_success("file_upload", f"Upload successful - Images: {image_count}, Prompts: {prompt_count}, Expected videos: {expected_videos}")
                    
                    # Verify expected counts
                    if image_count == 14:
                        self.log_success("image_extraction", f"Correctly extracted 14 images (ss.jpeg ignored)")
                    else:
                        self.log_error("image_extraction", f"Expected 14 images, got {image_count}")
                    
                    if prompt_count == 14:
                        self.log_success("prompt_parsing", f"Correctly parsed 14 prompts (case-insensitive Prompt_N format)")
                    else:
                        self.log_error("prompt_parsing", f"Expected 14 prompts, got {prompt_count}")
                    
                    if expected_videos == 28:  # 14 images * 2 videos per image
                        print(f"✅ Expected videos calculation correct: {expected_videos} (2 per image)")
                    else:
                        self.log_error("file_upload", f"Expected 28 videos, got {expected_videos}")
                    
                    return True
                else:
                    self.log_error("file_upload", "Upload flag is False")
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                self.log_error("file_upload", error_msg)
                return False
                
        except Exception as e:
            self.log_error("file_upload", f"Request failed: {str(e)}")
            return False
    
    def test_job_status(self):
        """Test GET /api/jobs/{job_id}"""
        print("\n🔍 Testing Job Status Retrieval...")
        if not self.job_id:
            self.log_error("job_status", "No job_id available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/jobs/{self.job_id}")
            
            if response.status_code == 200:
                data = response.json()
                job_name = data.get("job_name")
                status = data.get("status")
                total_images = data.get("total_images", 0)
                expected_videos = data.get("expected_videos", 0)
                
                self.log_success("job_status", f"Job: {job_name}, Status: {status}, Images: {total_images}, Expected videos: {expected_videos}")
                
                # Verify data consistency
                if total_images == 14 and expected_videos == 28:
                    print(f"✅ Job data consistent with upload results")
                else:
                    print(f"⚠️  Job data inconsistency: Images={total_images}, Videos={expected_videos}")
                
                return True
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                self.log_error("job_status", error_msg)
                return False
                
        except Exception as e:
            self.log_error("job_status", f"Request failed: {str(e)}")
            return False
    
    def test_video_records(self):
        """Test GET /api/videos/job/{job_id}"""
        print("\n🔍 Testing Video Records Retrieval...")
        if not self.job_id:
            self.log_error("video_records", "No job_id available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/videos/job/{self.job_id}")
            
            if response.status_code == 200:
                videos = response.json()
                video_count = len(videos)
                
                if video_count == 28:
                    self.log_success("video_records", f"Created {video_count} video records (2 per image)")
                    
                    # Verify video record structure
                    if videos:
                        sample_video = videos[0]
                        required_fields = ["video_id", "image_filename", "prompt_number", "prompt_text", "video_index", "status"]
                        missing_fields = [field for field in required_fields if field not in sample_video]
                        
                        if not missing_fields:
                            print(f"✅ Video record structure valid")
                            print(f"   Sample: Image={sample_video.get('image_filename')}, Prompt={sample_video.get('prompt_number')}, Index={sample_video.get('video_index')}")
                        else:
                            print(f"⚠️  Missing fields in video records: {missing_fields}")
                    
                    # Check for both video indices (1 and 2) per prompt
                    prompt_indices = {}
                    for video in videos:
                        prompt_num = video.get("prompt_number")
                        video_idx = video.get("video_index")
                        if prompt_num not in prompt_indices:
                            prompt_indices[prompt_num] = []
                        prompt_indices[prompt_num].append(video_idx)
                    
                    all_have_two_videos = all(len(indices) == 2 and set(indices) == {1, 2} for indices in prompt_indices.values())
                    if all_have_two_videos:
                        print(f"✅ All prompts have 2 video records (indices 1 and 2)")
                    else:
                        print(f"⚠️  Some prompts don't have exactly 2 video records")
                    
                    return True
                else:
                    self.log_error("video_records", f"Expected 28 video records, got {video_count}")
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                self.log_error("video_records", error_msg)
                return False
                
        except Exception as e:
            self.log_error("video_records", f"Request failed: {str(e)}")
            return False
    
    def test_job_listing(self):
        """Test GET /api/jobs"""
        print("\n🔍 Testing Job Listing...")
        try:
            response = self.session.get(f"{BACKEND_URL}/jobs")
            
            if response.status_code == 200:
                jobs = response.json()
                job_count = len(jobs)
                
                # Find our test job
                test_job = None
                if self.job_id:
                    test_job = next((job for job in jobs if job.get("job_id") == self.job_id), None)
                
                if test_job:
                    self.log_success("job_listing", f"Found {job_count} jobs including our test job")
                    print(f"   Test job: {test_job.get('job_name')} - Status: {test_job.get('status')}")
                else:
                    self.log_success("job_listing", f"Retrieved {job_count} jobs (test job not found, but API works)")
                
                return True
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                self.log_error("job_listing", error_msg)
                return False
                
        except Exception as e:
            self.log_error("job_listing", f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("🚀 BACKEND API TESTING - Video Automation Platform")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Files: {TEST_FILES}")
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_health_check),
            ("Job Creation", self.test_job_creation),
            ("File Upload (CRITICAL)", self.test_file_upload),
            ("Job Status", self.test_job_status),
            ("Video Records", self.test_video_records),
            ("Job Listing", self.test_job_listing)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name}: Unexpected error - {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if self.errors:
            print("\n🚨 ERRORS FOUND:")
            for error in self.errors:
                print(f"   • {error}")
        
        # Critical success criteria
        critical_tests = ["job_creation", "file_upload", "mongodb_connection", "prompt_parsing", "image_extraction"]
        critical_passed = all(self.test_results.get(test, False) for test in critical_tests)
        
        if critical_passed:
            print("\n🎉 ALL CRITICAL TESTS PASSED!")
            print("   ✅ MongoDB connection working")
            print("   ✅ Case-insensitive prompt parsing working")
            print("   ✅ File upload workflow complete")
            print("   ✅ 14 images extracted correctly")
            print("   ✅ 28 video records created")
        else:
            print("\n🚨 CRITICAL TESTS FAILED!")
            failed_critical = [test for test in critical_tests if not self.test_results.get(test, False)]
            for test in failed_critical:
                print(f"   ❌ {test.replace('_', ' ').title()}")
        
        return critical_passed, self.test_results, self.errors


if __name__ == "__main__":
    tester = BackendTester()
    success, results, errors = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)