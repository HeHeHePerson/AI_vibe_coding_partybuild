/*
智慧党建系统 - JavaScript
*/

// 全局变量
let currentUser = null;

// 工具函数
const utils = {
    // 显示提示消息
    showToast: function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // 格式化日期
    formatDate: function(dateStr) {
        if (!dateStr) return '';
        // 将空格替换为T，确保ISO格式兼容
        const dateStrFixed = dateStr.replace(' ', 'T');
        const date = new Date(dateStrFixed);
        if (isNaN(date.getTime())) return dateStr; // 如果解析失败，返回原始字符串
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 格式化日期(仅日期)
    formatDateOnly: function(dateStr) {
        if (!dateStr) return '';
        const dateStrFixed = dateStr.replace(' ', 'T');
        const date = new Date(dateStrFixed);
        if (isNaN(date.getTime())) return dateStr;
        return date.toLocaleDateString('zh-CN');
    },

    // 发送API请求
    api: async function(url, options = {}) {
        const defaultOptions = {
            credentials: 'same-origin'
        };
        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            return { code: 500, message: '网络请求失败' };
        }
    }
};

// 认证相关
const auth = {
    // 检查登录状态
    checkAuth: async function() {
        const result = await utils.api('/api/auth/check');
        if (result.logged_in) {
            currentUser = result.user;
            this.updateUI();
        } else {
            currentUser = null;
            this.updateUI();
        }
        return currentUser;
    },

    // 更新UI显示
    updateUI: function() {
        const userInfo = document.getElementById('userInfo');
        const navLinks = document.getElementById('navLinks');
        const loginBtn = document.getElementById('loginBtn');

        if (currentUser) {
            if (userInfo) {
                userInfo.innerHTML = `
                    <span class="username">${utils.escapeHtml(currentUser.username)}</span>
                    ${currentUser.role === 'admin' ? '<span class="role-badge admin">管理员</span>' : ''}
                    <a href="javascript:auth.logout()" class="btn btn-outline btn-sm">退出</a>
                `;
            }
            if (navLinks) {
                if (currentUser.role === 'admin') {
                    navLinks.innerHTML = `
                        <a href="/">首页</a>
                        <a href="/create">发布内容</a>
                        <a href="/manage">用户管理</a>
                    `;
                } else {
                    navLinks.innerHTML = `
                        <a href="/">首页</a>
                        <a href="/create">发布内容</a>
                    `;
                }
            }
        } else {
            if (userInfo) {
                userInfo.innerHTML = `
                    <a href="/login" class="btn btn-outline btn-sm">登录</a>
                    <a href="/register" class="btn btn-secondary btn-sm">注册</a>
                `;
            }
            if (navLinks) {
                navLinks.innerHTML = `<a href="/">首页</a>`;
            }
        }
    },

    // 登录
    login: async function(username, password) {
        const result = await utils.api('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (result.code === 200) {
            currentUser = result.data;
            this.updateUI();
            utils.showToast('登录成功', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } else {
            utils.showToast(result.message || '登录失败', 'error');
        }
    },

    // 注册
    register: async function(username, password) {
        const result = await utils.api('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (result.code === 200) {
            currentUser = result.data;
            this.updateUI();
            utils.showToast('注册成功', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } else {
            utils.showToast(result.message || '注册失败', 'error');
        }
    },

    // 登出
    logout: async function() {
        await utils.api('/api/auth/logout', { method: 'POST' });
        currentUser = null;
        this.updateUI();
        utils.showToast('已退出登录', 'info');
        setTimeout(() => {
            window.location.href = '/';
        }, 500);
    }
};

// 内容相关
const contents = {
    // 获取内容列表
    getList: async function() {
        const result = await utils.api('/api/contents');
        if (result.code === 200) {
            this.renderList(result.data);
        } else {
            utils.showToast('获取内容列表失败', 'error');
        }
    },

    // 渲染内容列表
    renderList: function(contents) {
        const listContainer = document.getElementById('contentList');
        if (!listContainer) return;

        if (!contents || contents.length === 0) {
            listContainer.innerHTML = '<div class="content-item"><p style="text-align:center;color:#999;">暂无内容</p></div>';
            return;
        }

        listContainer.innerHTML = contents.map(content => `
            <div class="content-item" onclick="window.location.href='/content/${content.id}'">
                <h2>${content.title}</h2>
                <div class="meta">
                    <span>作者: ${utils.escapeHtml(content.author_name)}</span>
                    <span>发布时间: ${utils.formatDate(content.created_at)}</span>
                </div>
            </div>
        `).join('');
    },

    // 获取内容详情
    getDetail: async function(contentId) {
        const result = await utils.api(`/api/contents/${contentId}`);
        if (result.code === 200) {
            this.renderDetail(result.data);
        } else {
            utils.showToast(result.message || '获取内容详情失败', 'error');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    },

    // 渲染内容详情
    renderDetail: function(data) {
        const { content, comments, like_count, user_liked } = data;

        // 渲染内容
        const contentContainer = document.getElementById('contentDetail');
        if (contentContainer) {
            // 处理附件显示
            let attachmentsHtml = '';
            if (content.images && content.images.length > 0) {
                const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'];
                let imagesPart = '';
                let filesPart = '';

                content.images.forEach(file => {
                    const ext = file.split('.').pop().toLowerCase();
                    const filename = file.split('/').pop();
                    if (imageExtensions.includes(ext)) {
                        // 图片文件
                        imagesPart += `<img src="${utils.escapeHtml(file)}" alt="图片">`;
                    } else {
                        // 文档文件显示为下载链接
                        filesPart += `<div class="file-item">
                            <a href="${utils.escapeHtml(file)}" target="_blank" class="file-link">
                                <span class="file-icon">📄</span>
                                ${utils.escapeHtml(decodeURIComponent(filename))}
                            </a>
                        </div>`;
                    }
                });

                attachmentsHtml = '<div class="attachments">';
                if (imagesPart) {
                    attachmentsHtml += '<div class="images">' + imagesPart + '</div>';
                }
                if (filesPart) {
                    attachmentsHtml += '<div class="files"><h4>附件：</h4>' + filesPart + '</div>';
                }
                attachmentsHtml += '</div>';
            }

            contentContainer.innerHTML = `
                <h1>${utils.escapeHtml(content.title)}</h1>
                <div class="meta">
                    <span>作者: ${utils.escapeHtml(content.author_name)}</span>
                    <span>发布时间: ${utils.formatDate(content.created_at)}</span>
                </div>
                <div class="body">${utils.escapeHtml(content.body).replace(/\n/g, '<br>')}</div>
                ${attachmentsHtml}
            `;
        }

        // 渲染点赞按钮
        const likeBtn = document.getElementById('likeBtn');
        if (likeBtn) {
            if (!currentUser) {
                likeBtn.innerHTML = `<span>点赞数: ${like_count}</span>`;
            } else {
                likeBtn.innerHTML = user_liked
                    ? `<span class="liked">已点赞 (${like_count})</span>`
                    : `<span>点赞 (${like_count})</span>`;
                likeBtn.onclick = () => contents.toggleLike(content.id, user_liked);
            }
        }

        // 渲染评论
        this.renderComments(comments, content.author_id);

        // 检查删除权限
        const deleteBtn = document.getElementById('deleteBtn');
        if (deleteBtn && currentUser) {
            if (currentUser.id === content.author_id || currentUser.role === 'admin') {
                deleteBtn.style.display = 'inline-block';
                deleteBtn.onclick = () => contents.deleteContent(content.id);
            } else {
                deleteBtn.style.display = 'none';
            }
        }
    },

    // 渲染评论列表
    renderComments: function(comments, authorId) {
        const commentsContainer = document.getElementById('commentsList');
        if (!commentsContainer) return;

        if (!comments || comments.length === 0) {
            commentsContainer.innerHTML = '<p style="color:#999;text-align:center;">暂无评论</p>';
        } else {
            commentsContainer.innerHTML = comments.map(comment => {
                const canDelete = currentUser && (currentUser.id === comment.user_id || currentUser.role === 'admin');
                const canLike = currentUser !== null;
                const likeBtnHtml = canLike
                    ? (comment.user_liked
                        ? `<button class="comment-like-btn liked" onclick="contents.toggleCommentLike(${comment.id}, true)">赞 (${comment.like_count || 0})</button>`
                        : `<button class="comment-like-btn" onclick="contents.toggleCommentLike(${comment.id}, false)">赞 (${comment.like_count || 0})</button>`)
                    : `<span class="comment-like-count">赞 (${comment.like_count || 0})</span>`;
                return `
                    <div class="comment-item" data-id="${comment.id}">
                        <div class="comment-header">
                            <span class="comment-author">${utils.escapeHtml(comment.user_name)}</span>
                            <span class="comment-time">${utils.formatDate(comment.created_at)}</span>
                        </div>
                        <div class="comment-body">${utils.escapeHtml(comment.body).replace(/\n/g, '<br>')}</div>
                        <div class="comment-actions">
                            ${likeBtnHtml}
                            ${canDelete ? `<button class="btn btn-danger btn-sm" onclick="contents.deleteComment(${comment.id})">删除</button>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // 评论表单显示（始终检查，当前用户登录时显示）
        const commentForm = document.getElementById('commentForm');
        if (commentForm) {
            if (currentUser) {
                commentForm.style.display = 'block';
            } else {
                commentForm.style.display = 'none';
            }
        }
    },

    // 切换评论点赞
    toggleCommentLike: async function(commentId, currentlyLiked) {
        if (!currentUser) {
            window.location.href = '/login';
            return;
        }

        let result;
        if (currentlyLiked) {
            // 取消点赞
            result = await utils.api(`/api/comments/${commentId}/like`, {
                method: 'DELETE'
            });
        } else {
            // 添加点赞
            result = await utils.api(`/api/comments/${commentId}/like`, {
                method: 'POST'
            });
        }

        if (result.code === 200) {
            // 刷新页面以更新点赞状态
            const contentId = window.location.pathname.split('/').pop();
            this.getDetail(contentId);
        } else {
            utils.showToast(result.message || '操作失败', 'error');
        }
    },

    // 添加评论
    addComment: async function(contentId) {
        if (!currentUser) {
            window.location.href = '/login';
            return;
        }

        const body = document.getElementById('commentBody').value.trim();
        if (!body) {
            utils.showToast('评论内容不能为空', 'error');
            return;
        }

        const result = await utils.api(`/api/contents/${contentId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ body })
        });

        if (result.code === 200) {
            utils.showToast('评论成功', 'success');
            document.getElementById('commentBody').value = '';
            this.getDetail(contentId); // 刷新详情页
        } else {
            utils.showToast(result.message || '评论失败', 'error');
        }
    },

    // 删除评论
    deleteComment: async function(commentId) {
        if (!confirm('确定要删除这条评论吗?')) return;

        const result = await utils.api(`/api/comments/${commentId}`, {
            method: 'DELETE'
        });

        if (result.code === 200) {
            utils.showToast('删除成功', 'success');
            // 刷新当前页面
            const contentId = window.location.pathname.split('/').pop();
            this.getDetail(contentId);
        } else {
            utils.showToast(result.message || '删除失败', 'error');
        }
    },

    // 点赞/取消点赞
    toggleLike: async function(contentId, alreadyLiked) {
        if (!currentUser) {
            window.location.href = '/login';
            return;
        }

        let result;
        if (alreadyLiked) {
            result = await utils.api(`/api/contents/${contentId}/like`, { method: 'DELETE' });
        } else {
            result = await utils.api(`/api/contents/${contentId}/like`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (result.code === 200) {
            this.getDetail(contentId);
        } else {
            utils.showToast(result.message || '操作失败', 'error');
        }
    },

    // 删除内容
    deleteContent: async function(contentId) {
        if (!confirm('确定要删除这篇内容吗？此操作不可恢复！')) return;

        const result = await utils.api(`/api/contents/${contentId}`, {
            method: 'DELETE'
        });

        if (result.code === 200) {
            utils.showToast('删除成功', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } else {
            utils.showToast(result.message || '删除失败', 'error');
        }
    },

    // 创建内容
    create: async function(formData) {
        const result = await utils.api('/api/contents', {
            method: 'POST',
            body: formData
        });

        if (result.code === 200) {
            utils.showToast('发布成功', 'success');
            setTimeout(() => {
                window.location.href = `/content/${result.data.id}`;
            }, 500);
        } else {
            utils.showToast(result.message || '发布失败', 'error');
        }
    }
};

// 统计相关
const stats = {
    // 获取访问统计
    getStats: async function() {
        const result = await utils.api('/api/stats/visits');
        if (result.code === 200) {
            this.renderStats(result.data);
        }
    },

    // 渲染统计数据
    renderStats: function(data) {
        const todayEl = document.getElementById('todayCount');
        const monthEl = document.getElementById('monthCount');
        const totalEl = document.getElementById('totalCount');

        if (todayEl) todayEl.textContent = data.today || 0;
        if (monthEl) monthEl.textContent = data.month || 0;
        if (totalEl) totalEl.textContent = data.total || 0;
    }
};

// 用户管理相关
const userManage = {
    // 获取用户列表
    getUsers: async function() {
        const result = await utils.api('/api/users');
        if (result.code === 200) {
            this.renderUsers(result.data);
        } else if (result.code === 401 || result.code === 403) {
            window.location.href = '/login';
        } else {
            utils.showToast(result.message || '获取用户列表失败', 'error');
        }
    },

    // 渲染用户列表
    renderUsers: function(users) {
        const tbody = document.getElementById('userTableBody');
        if (!tbody) return;

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${utils.escapeHtml(user.username)}</td>
                <td><span class="role-badge ${user.role}">${user.role === 'admin' ? '管理员' : '普通用户'}</span></td>
                <td>${utils.formatDate(user.created_at)}</td>
                <td>
                    ${user.role !== 'admin' ? `<button class="btn btn-danger btn-sm" onclick="userManage.deleteUser(${user.id})">删除</button>` : '-'}
                </td>
            </tr>
        `).join('');
    },

    // 创建用户
    createUser: async function(username, password, role) {
        const result = await utils.api('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        if (result.code === 200) {
            utils.showToast('创建成功', 'success');
            this.getUsers();
            document.getElementById('addUserForm').reset();
            document.getElementById('addUserModal').classList.remove('show');
        } else {
            utils.showToast(result.message || '创建失败', 'error');
        }
    },

    // 删除用户
    deleteUser: async function(userId) {
        if (!confirm('确定要删除该用户吗？')) return;

        const result = await utils.api(`/api/users/${userId}`, {
            method: 'DELETE'
        });

        if (result.code === 200) {
            utils.showToast('删除成功', 'success');
            this.getUsers();
        } else {
            utils.showToast(result.message || '删除失败', 'error');
        }
    }
};

// HTML转义
utils.escapeHtml = function(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    auth.checkAuth();
});
