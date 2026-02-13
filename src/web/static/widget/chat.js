/**
 * 두온교육 AI 채팅 위젯 — v2 (인라인 CSS)
 * 임베드: <script src="https://HOST/widget/chat.js" data-api="https://HOST" async></script>
 */
(function(){
  'use strict';

  var script = document.currentScript || (function(){
    var scripts = document.getElementsByTagName('script');
    for(var i=scripts.length-1;i>=0;i--){
      if(scripts[i].src && scripts[i].src.indexOf('chat.js')!==-1) return scripts[i];
    }
  })();
  var API_BASE = (script && script.getAttribute('data-api')) || '';

  // 인라인 CSS 삽입 (캐시 문제 방지)
  var style = document.createElement('style');
  style.textContent = '\
#duon-chat-widget{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",sans-serif!important;font-size:14px!important;line-height:1.6!important;color:#333!important;z-index:99999!important}\
#duon-chat-widget *{box-sizing:border-box!important}\
#duon-chat-widget .duon-chat-btn{position:fixed!important;bottom:24px!important;right:24px!important;width:56px!important;height:56px!important;border-radius:50%!important;background:#5b8def!important;color:#fff!important;border:none!important;cursor:pointer!important;box-shadow:0 3px 12px rgba(91,141,239,.4)!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:24px!important;transition:all .25s ease!important;z-index:99999!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-btn:hover{transform:scale(1.05)!important;box-shadow:0 5px 20px rgba(91,141,239,.5)!important}\
#duon-chat-widget .duon-chat-btn.active{transform:scale(0)!important;opacity:0!important;pointer-events:none!important}\
#duon-chat-widget .duon-chat-window{position:fixed!important;bottom:92px!important;right:24px!important;width:380px!important;height:560px!important;background:#fff!important;border-radius:20px!important;box-shadow:0 6px 30px rgba(0,0,0,.12),0 1px 4px rgba(0,0,0,.06)!important;display:flex!important;flex-direction:column!important;overflow:hidden!important;opacity:0!important;transform:translateY(16px) scale(.96)!important;transition:all .3s cubic-bezier(.4,0,.2,1)!important;pointer-events:none!important;z-index:99999!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-window.open{opacity:1!important;transform:translateY(0) scale(1)!important;pointer-events:auto!important}\
#duon-chat-widget .duon-chat-header{background:#1b3a5c!important;color:#fff!important;padding:16px 20px!important;display:flex!important;align-items:center!important;justify-content:space-between!important;flex-shrink:0!important;margin:0!important}\
#duon-chat-widget .duon-chat-header-left{display:flex!important;align-items:center!important;gap:10px!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-avatar{width:32px!important;height:32px!important;border-radius:50%!important;background:rgba(255,255,255,.18)!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:15px!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-header-title{font-size:14px!important;font-weight:600!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-header-subtitle{display:none!important}\
#duon-chat-widget .duon-chat-header-actions{display:flex!important;gap:8px!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-close,#duon-chat-widget .duon-chat-refresh{background:none!important;border:none!important;color:rgba(255,255,255,.65)!important;width:28px!important;height:28px!important;border-radius:6px!important;cursor:pointer!important;font-size:16px!important;display:flex!important;align-items:center!important;justify-content:center!important;transition:color .15s!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-close:hover,#duon-chat-widget .duon-chat-refresh:hover{color:#fff!important}\
#duon-chat-widget .duon-chat-messages{flex:1!important;overflow-y:auto!important;padding:24px 20px!important;display:flex!important;flex-direction:column!important;gap:14px!important;background:#fff!important;margin:0!important}\
#duon-chat-widget .duon-chat-messages::-webkit-scrollbar{width:0!important}\
#duon-chat-widget .duon-msg{max-width:85%!important;padding:14px 18px!important;word-break:break-word!important;font-size:14px!important;line-height:1.65!important;animation:duon-fade .2s ease!important;margin:0!important}\
#duon-chat-widget .duon-msg-ai{align-self:flex-start!important;background:#f4f4f4!important;color:#333!important;border-radius:4px 18px 18px 18px!important;border:none!important}\
#duon-chat-widget .duon-msg-user{align-self:flex-end!important;background:#1b3a5c!important;color:#fff!important;border-radius:18px 4px 18px 18px!important;border:none!important}\
#duon-chat-widget .duon-typing{align-self:flex-start!important;background:#f4f4f4!important;padding:14px 20px!important;border-radius:4px 18px 18px 18px!important;display:flex!important;gap:5px!important;align-items:center!important;margin:0!important}\
#duon-chat-widget .duon-typing-dot{width:7px!important;height:7px!important;border-radius:50%!important;background:#bbb!important;animation:duon-bounce .6s infinite alternate!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-typing-dot:nth-child(2){animation-delay:.15s!important}\
#duon-chat-widget .duon-typing-dot:nth-child(3){animation-delay:.3s!important}\
#duon-chat-widget .duon-quick-actions{display:flex!important;flex-wrap:wrap!important;gap:8px!important;padding:0 20px 16px!important;background:#fff!important;margin:0!important}\
#duon-chat-widget .duon-quick-btn{background:#fff!important;border:1px solid #d0d0d0!important;border-radius:20px!important;padding:8px 16px!important;font-size:13px!important;color:#444!important;cursor:pointer!important;transition:all .15s!important;font-family:inherit!important;margin:0!important}\
#duon-chat-widget .duon-quick-btn:hover{background:#1b3a5c!important;color:#fff!important;border-color:#1b3a5c!important}\
#duon-chat-widget .duon-chat-input-area{display:flex!important;padding:14px 16px 16px!important;gap:12px!important;flex-shrink:0!important;background:#eaf1fb!important;align-items:center!important;margin:0!important}\
#duon-chat-widget .duon-chat-input{flex:1!important;border:none!important;border-radius:24px!important;padding:12px 18px!important;font-size:14px!important;outline:none!important;font-family:inherit!important;background:#fff!important;color:#333!important;margin:0!important}\
#duon-chat-widget .duon-chat-input::placeholder{color:#aaa!important}\
#duon-chat-widget .duon-chat-input:focus{box-shadow:0 0 0 2px rgba(91,141,239,.2)!important}\
#duon-chat-widget .duon-chat-send{width:48px!important;height:48px!important;border-radius:50%!important;background:#5b8def!important;color:#fff!important;border:none!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;transition:all .15s!important;flex-shrink:0!important;font-size:20px!important;box-shadow:0 2px 8px rgba(91,141,239,.3)!important;margin:0!important;padding:0!important}\
#duon-chat-widget .duon-chat-send:hover{background:#4a7de0!important}\
#duon-chat-widget .duon-chat-send:disabled{background:#ccc!important;cursor:not-allowed!important;box-shadow:none!important}\
#duon-chat-widget .duon-chat-footer{display:none!important}\
@keyframes duon-fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}\
@keyframes duon-bounce{from{transform:translateY(0)}to{transform:translateY(-6px)}}\
@media(max-width:480px){#duon-chat-widget .duon-chat-window{bottom:0!important;right:0!important;width:100%!important;height:100%!important;border-radius:0!important}#duon-chat-widget .duon-chat-btn{bottom:16px!important;right:16px!important;width:50px!important;height:50px!important;font-size:20px!important}}\
';
  document.head.appendChild(style);

  var SESSION_KEY='duon_chat_sid';
  function getSid(){try{return localStorage.getItem(SESSION_KEY)||''}catch(e){return''}}
  function setSid(s){try{localStorage.setItem(SESSION_KEY,s)}catch(e){}}

  var QUICK_ACTIONS = [
    {text: '어떤 도서를 출판하나요?', msg: '어떤 도서를 출판하나요?'},
    {text: '출판 문의는 어떻게 하나요?', msg: '출판 문의는 어떻게 하나요?'},
    {text: '교육 프로그램 안내', msg: '교육 프로그램에 대해 알려주세요'},
  ];

  function build(){
    var root=document.createElement('div');root.id='duon-chat-widget';

    var btn=document.createElement('button');btn.className='duon-chat-btn';btn.innerHTML='💬';btn.setAttribute('aria-label','채팅 열기');
    root.appendChild(btn);

    var win=document.createElement('div');win.className='duon-chat-window';
    win.innerHTML=
      '<div class="duon-chat-header">'+
        '<div class="duon-chat-header-left">'+
          '<div class="duon-chat-avatar">💬</div>'+
          '<div class="duon-chat-header-info">'+
            '<div class="duon-chat-header-title">두온교육 AI 어시스턴트</div>'+
          '</div>'+
        '</div>'+
        '<div class="duon-chat-header-actions">'+
          '<button class="duon-chat-refresh" aria-label="새로고침">↻</button>'+
          '<button class="duon-chat-close" aria-label="닫기">✕</button>'+
        '</div>'+
      '</div>'+
      '<div class="duon-chat-messages"></div>'+
      '<div class="duon-quick-actions"></div>'+
      '<div class="duon-chat-input-area">'+
        '<input class="duon-chat-input" type="text" placeholder="메시지를 입력하세요..." maxlength="500">'+
        '<button class="duon-chat-send" aria-label="전송">➤</button>'+
      '</div>';
    root.appendChild(win);
    document.body.appendChild(root);

    var msgs=win.querySelector('.duon-chat-messages');
    var input=win.querySelector('.duon-chat-input');
    var sendBtn=win.querySelector('.duon-chat-send');
    var closeBtn=win.querySelector('.duon-chat-close');
    var refreshBtn=win.querySelector('.duon-chat-refresh');
    var quickArea=win.querySelector('.duon-quick-actions');
    var isOpen=false;
    var sending=false;

    function buildQuickActions(){
      quickArea.innerHTML='';
      QUICK_ACTIONS.forEach(function(qa){
        var b=document.createElement('button');
        b.className='duon-quick-btn';
        b.textContent=qa.text;
        b.addEventListener('click',function(){
          input.value=qa.msg;
          send();
          quickArea.style.display='none';
        });
        quickArea.appendChild(b);
      });
    }
    buildQuickActions();

    function toggle(){
      isOpen=!isOpen;
      win.classList.toggle('open',isOpen);
      btn.classList.toggle('active',isOpen);
      if(isOpen) input.focus();
    }

    btn.addEventListener('click',toggle);
    closeBtn.addEventListener('click',toggle);
    refreshBtn.addEventListener('click',function(){
      msgs.innerHTML='';
      quickArea.style.display='flex';
      buildQuickActions();
      try{localStorage.removeItem(SESSION_KEY)}catch(e){}
      addMsg('안녕하세요! 두온교육 AI 어시스턴트입니다. 도서, 출판, 문의 등 무엇이든 물어보세요.','ai');
    });

    function addMsg(text,role){
      var el=document.createElement('div');
      el.className='duon-msg duon-msg-'+role;
      el.innerHTML=text.replace(/\n/g,'<br>');
      msgs.appendChild(el);
      msgs.scrollTop=msgs.scrollHeight;
      return el;
    }

    function showTyping(){
      var el=document.createElement('div');el.className='duon-typing';el.id='duon-typing';
      el.innerHTML='<span class="duon-typing-dot"></span><span class="duon-typing-dot"></span><span class="duon-typing-dot"></span>';
      msgs.appendChild(el);msgs.scrollTop=msgs.scrollHeight;
    }
    function hideTyping(){var el=document.getElementById('duon-typing');if(el)el.remove();}

    function send(){
      var text=input.value.trim();
      if(!text||sending)return;
      addMsg(text,'user');
      input.value='';
      sending=true;sendBtn.disabled=true;
      quickArea.style.display='none';
      showTyping();

      var body=JSON.stringify({message:text,session_id:getSid()||undefined});
      fetch(API_BASE+'/api/chat',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:body
      })
      .then(function(r){
        if(r.status===429) throw new Error('rate');
        if(!r.ok) throw new Error('err');
        return r.json();
      })
      .then(function(data){
        hideTyping();
        addMsg(data.reply,'ai');
        if(data.session_id) setSid(data.session_id);
      })
      .catch(function(e){
        hideTyping();
        if(e.message==='rate'){
          addMsg('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.','ai');
        }else{
          addMsg('죄송합니다, 일시적인 오류가 발생했습니다. 다시 시도해주세요.','ai');
        }
      })
      .finally(function(){sending=false;sendBtn.disabled=false;input.focus();});
    }

    sendBtn.addEventListener('click',send);
    input.addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});

    addMsg('안녕하세요! 두온교육 AI 어시스턴트입니다. 도서, 출판, 문의 등 무엇이든 물어보세요.','ai');
  }

  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',build);}else{build();}
})();
