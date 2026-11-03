import json, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== عدل هنا فقط ==========
TOKEN = "7982223412:AAHj8Ld7NbK2mEJJRjaxUNKtH-CkRnYHq5I"
ADMIN_ID = 1955617835
SHOP_NAME = "Pro Max"
SHOP_USER = "@ProMax"
PAYMENT_INFO = "الدفع: حوالة - كريمي - أم فلوس"
# =================================

FILE = "pro_max_data.json"

def default_data():
    return {
        "offers": ["🔥 خصم 20% على كل خدمات Pro Max"],
        "services": [
            {"id": 1, "name": "اشتراك VIP شهري", "price": "5000 ريال", "desc": "اشتراك VIP كامل"},
            {"id": 2, "name": "شحن ألعاب", "price": "حسب الكمية", "desc": "شحن سريع"},
            {"id": 3, "name": "اشتراك نتفلكس", "price": "3000 ريال", "desc": "حساب خاص وضمان"},
        ],
        "orders": [], "users": [],
        "next_service_id": 4,
        "merchants": {},
        "listings": [],
        "next_listing_id": 1,
        "tasks": [],
        "next_task_id": 1,
        "points": {},
        "submissions": [],
        "next_sub_id": 1,
    }

def load():
    if not os.path.exists(FILE):
        d = default_data(); save(d); return d
    with open(FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    for k,v in default_data().items():
        if k not in d: d[k]=v
    return d

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load()

def pts(uid): return data["points"].get(str(uid), 0)
def add_pts(uid, n):
    data["points"][str(uid)] = pts(uid)+n
    save(data)

def main_menu(is_admin=False):
    kb = [
        [InlineKeyboardButton("🔥 عروض اليوم", callback_data="offers")],
        [InlineKeyboardButton("💎 متجر Pro Max", callback_data="services")],
        [InlineKeyboardButton("🏛️ متجر النقابة - لوحة التاجر", callback_data="guild")],
        [InlineKeyboardButton("🎯 قسم المهام والنقاط", callback_data="tasks_menu")],
        [InlineKeyboardButton("🛒 اطلب خدمة", callback_data="order_start")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton("⭐ نقاطي", callback_data="my_points")],
        [InlineKeyboardButton("📞 تواصل معنا", callback_data="contact")],
    ]
    if is_admin:
        kb.append([InlineKeyboardButton("👑 لوحة تحكم الادمن", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def back_menu(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back")]])
def back_guild(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للنقابة", callback_data="guild")],[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back")]])
def back_tasks(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للمهام", callback_data="tasks_menu")],[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back")]])

def admin_menu():
    kb = [
        [InlineKeyboardButton("➕ إضافة خدمة", callback_data="admin_add_service")],
        [InlineKeyboardButton("🗑️ حذف خدمة", callback_data="admin_del_service")],
        [InlineKeyboardButton("🔥 إضافة عرض", callback_data="admin_add_offer")],
        [InlineKeyboardButton("🎯 إضافة مهمة جديدة", callback_data="admin_add_task")],
        [InlineKeyboardButton("📝 مراجعة إثباتات المهام", callback_data="admin_review_tasks")],
        [InlineKeyboardButton("🏛️ مراجعة خدمات التجار", callback_data="admin_listings")],
        [InlineKeyboardButton("📦 كل الطلبات", callback_data="admin_orders")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📣 بث للكل", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in data["users"]:
        data["users"].append(user.id); save(data)
    context.user_data.clear()
    is_admin = user.id == ADMIN_ID
    text = f"أهلاً بك في {SHOP_NAME} 👑\n\n🏛️ متجر النقابة: بيع واشتري من التجار\n🎯 المهام: نفذ مهام واجمع نقاط وبدلها\n\nنقاطك الآن: {pts(user.id)} ⭐\n\nاختر 👇"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(is_admin))
    elif update.callback_query:
        try: await update.callback_query.edit_message_text(text, reply_markup=main_menu(is_admin))
        except: await update.callback_query.message.reply_text(text, reply_markup=main_menu(is_admin))

async def guild_menu(q, uid):
    is_merchant = str(uid) in data["merchants"]
    m = data["merchants"].get(str(uid), {})
    txt = "🏛️ متجر النقابة\n\nهنا التجار يعرضوا خدماتهم، وانت تقدر تبيع وتشتري.\n"
    if is_merchant:
        txt += f"\n✅ انت تاجر: {m['shop_name']}\n📦 مبيعاتك: {m.get('sales',0)}"
    else:
        txt += "\nانت لسه مش تاجر، سجل وابدأ تبيع."
    kb = [
        [InlineKeyboardButton("🛍️ تصفح خدمات التجار", callback_data="marketplace")],
        [InlineKeyboardButton("🏪 لوحة التاجر", callback_data="merchant_panel")],
    ]
    if not is_merchant:
        kb.append([InlineKeyboardButton("📝 سجل كتاجر الآن", callback_data="become_merchant")])
    kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def merchant_panel(q, uid):
    m = data["merchants"].get(str(uid))
    if not m:
        await q.edit_message_text("انت مش تاجر بعد.\nاضغط سجل كتاجر أولاً.", reply_markup=back_guild()); return
    my = [x for x in data["listings"] if x["seller_id"]==uid]
    txt = f"🏪 لوحة التاجر\n\nمتجرك: {m['shop_name']}\nاسمك: {m['name']}\n📦 خدماتك المعروضة: {len(my)}\n💰 مبيعاتك: {m.get('sales',0)}"
    kb = [
        [InlineKeyboardButton("➕ أضف خدمة للبيع", callback_data="add_listing")],
        [InlineKeyboardButton("📦 خدماتي المعروضة", callback_data="my_listings")],
        [InlineKeyboardButton("🗑️ حذف خدمة لي", callback_data="del_my_listing")],
        [InlineKeyboardButton("🔙 رجوع للنقابة", callback_data="guild")],
    ]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def tasks_menu(q, uid):
    txt = f"🎯 قسم المهام\n\n⭐ نقاطك: {pts(uid)}\n\nنفذ المهام، ارسل إثبات، والادمن يوافق وتاخذ النقاط.\n\nالمهام المتاحة:"
    if not data["tasks"]:
        txt += "\n\nلا توجد مهام حالياً، ارجع قريب."
    else:
        for t in data["tasks"]:
            if t["active"]:
                txt += f"\n\n▫️ {t['title']}\n⭐ النقاط: {t['points']} | 📝 {t['desc']}"
    kb = [
        [InlineKeyboardButton("✅ اختر مهمة ونفذها", callback_data="do_task")],
        [InlineKeyboardButton("📝 إثباتاتي", callback_data="my_submissions")],
        [InlineKeyboardButton("🏆 ترتيب النقاط", callback_data="leaderboard")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; d = q.data
    if d == "back": await start(update, context); return
    if d == "my_points":
        await q.edit_message_text(f"⭐ نقاطك: {pts(uid)}\n\nاجمع نقاط من المهام، واطلب من الادمن تبديلها بخصم أو خدمة.", reply_markup=back_menu()); return
    if d == "contact":
        await q.edit_message_text(f"📞 تواصل:\n{SHOP_USER}\n\n{PAYMENT_INFO}", reply_markup=back_menu()); return
    if d == "offers":
        offers = "\n\n".join(data["offers"]) if data["offers"] else "لا توجد عروض"
        await q.edit_message_text(f"🔥 عروض {SHOP_NAME}:\n\n{offers}", reply_markup=back_menu()); return
    if d == "services":
        txt = "💎 متجر Pro Max:\n\n"
        for s in data["services"]: txt += f"▫️ {s['name']} - {s['price']}\n{s['desc']}\n\n"
        kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']}", callback_data=f"buy_{s['id']}")] for s in data["services"]]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb)); return
    if d == "order_start":
        kb = [[InlineKeyboardButton(f"{s['name']}", callback_data=f"buy_{s['id']}")] for s in data["services"]]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        await q.edit_message_text("🛒 اختر خدمة تطلبها:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d == "my_orders":
        my = [o for o in data["orders"] if o["user_id"]==uid]
        txt = "📦 طلباتك:\n\n" + "\n".join([f"▫️ {o['service']} - {o['status']}" for o in my[-10:]]) if my else "ما عندك طلبات"
        await q.edit_message_text(txt, reply_markup=back_menu()); return
    if d.startswith("buy_"):
        sid = int(d.split("_")[1]); s = next((x for x in data["services"] if x["id"]==sid), None)
        if s:
            context.user_data["waiting_order"] = s["name"]
            await q.edit_message_text(f"🛒 اخترت: {s['name']}\n💰 {s['price']}\n\nاكتب اسمك + رقمك:", reply_markup=back_menu())
        return
    if d == "guild": await guild_menu(q, uid); return
    if d == "merchant_panel": await merchant_panel(q, uid); return
    if d == "become_merchant":
        context.user_data["waiting_merchant"] = True
        await q.edit_message_text("🏛️ التسجيل كتاجر\n\nأرسل اسم متجرك بهذا الشكل:\n\nاسمك | اسم متجرك\n\nمثال:\nأيمن | متجر أيمن برو", reply_markup=back_guild()); return
    if d == "add_listing":
        if str(uid) not in data["merchants"]:
            await q.edit_message_text("سجل كتاجر أولاً", reply_markup=back_guild()); return
        context.user_data["waiting_listing"] = True
        await q.edit_message_text("➕ أضف خدمتك للبيع\n\nأرسل بهذا الشكل:\nالاسم | السعر | الوصف", reply_markup=back_guild()); return
    if d == "marketplace":
        active = [x for x in data["listings"] if x["active"]]
        if not active:
            await q.edit_message_text("🏛️ متجر النقابة فاضي لسه، كن أول تاجر يعرض.", reply_markup=back_guild()); return
        kb = []
        for x in active:
            kb.append([InlineKeyboardButton(f"{x['name']} - {x['price']} | {x['shop']}", callback_data=f"view_listing_{x['id']}")])
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="guild")])
        await q.edit_message_text("🛍️ خدمات التجار في النقابة:\n\nاضغط أي خدمة للشراء:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("view_listing_"):
        lid = int(d.split("_")[2]); x = next((i for i in data["listings"] if i["id"]==lid), None)
        if x:
            kb = [[InlineKeyboardButton("🛒 اطلب هذي الخدمة", callback_data=f"buy_listing_{lid}")],[InlineKeyboardButton("🔙 رجوع", callback_data="marketplace")]]
            await q.edit_message_text(f"🏛️ {x['name']}\n\n🏪 المتجر: {x['shop']}\n💰 السعر: {x['price']}\n📝 {x['desc']}\n\n{PAYMENT_INFO}", reply_markup=InlineKeyboardMarkup(kb))
        return
    if d.startswith("buy_listing_"):
        lid = int(d.split("_")[2]); x = next((i for i in data["listings"] if i["id"]==lid), None)
        if x:
            context.user_data["waiting_buy_listing"] = x
            await q.edit_message_text(f"🛒 تطلب من: {x['shop']}\nخدمة: {x['name']}\n\nاكتب اسمك + رقمك:", reply_markup=back_guild())
        return
    if d == "my_listings":
        my = [x for x in data["listings"] if x["seller_id"]==uid]
        txt = "📦 خدماتك:\n\n" + "\n".join([f"▫️ {x['name']} - {x['price']}" for x in my]) if my else "ما عندك خدمات"
        await q.edit_message_text(txt, reply_markup=back_guild()); return
    if d == "del_my_listing":
        my = [x for x in data["listings"] if x["seller_id"]==uid]
        if not my:
            await q.edit_message_text("ما عندك خدمات", reply_markup=back_guild()); return
        kb = [[InlineKeyboardButton(f"🗑️ {x['name']}", callback_data=f"del_listing_{x['id']}")] for x in my]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="merchant_panel")])
        await q.edit_message_text("اختر للحذف:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("del_listing_"):
        lid = int(d.split("_")[2]); data["listings"] = [x for x in data["listings"] if x["id"]!=lid]; save(data)
        await q.edit_message_text("✅ تم الحذف", reply_markup=back_guild()); return
    if d == "tasks_menu": await tasks_menu(q, uid); return
    if d == "do_task":
        active = [t for t in data["tasks"] if t["active"]]
        if not active:
            await q.edit_message_text("لا توجد مهام حالياً", reply_markup=back_tasks()); return
        kb = [[InlineKeyboardButton(f"{t['title']} - {t['points']} ⭐", callback_data=f"start_task_{t['id']}")] for t in active]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="tasks_menu")])
        await q.edit_message_text("اختر مهمة:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("start_task_"):
        tid = int(d.split("_")[2]); t = next((x for x in data["tasks"] if x["id"]==tid), None)
        if t:
            context.user_data["waiting_task_proof"] = tid
            await q.edit_message_text(f"🎯 المهمة: {t['title']}\n\n📝 المطلوب: {t['desc']}\n⭐ النقاط: {t['points']}\n\nنفذها، وبعدين أرسل إثبات هنا.", reply_markup=back_tasks())
        return
    if d == "my_submissions":
        my = [s for s in data["submissions"] if s["user_id"]==uid]
        txt = "📝 إثباتاتك:\n\n" + "\n".join([f"▫️ مهمة {s['task_title']} - {s['status']}" for s in my[-10:]]) if my else "ما قدمت أي إثبات"
        await q.edit_message_text(txt, reply_markup=back_tasks()); return
    if d == "leaderboard":
        sorted_pts = sorted(data["points"].items(), key=lambda x: x[1], reverse=True)[:10]
        txt = "🏆 ترتيب النقاط:\n\n"
        for i,(u,p) in enumerate(sorted_pts,1):
            txt += f"{i}. {p} ⭐ - {u}\n"
        if not sorted_pts: txt += "لسه ما حد جمع نقاط"
        await q.edit_message_text(txt, reply_markup=back_tasks()); return
    if d == "admin_panel":
        if uid != ADMIN_ID: return
        await q.edit_message_text("👑 لوحة تحكم Pro Max", reply_markup=admin_menu()); return
    if d == "admin_stats":
        if uid != ADMIN_ID: return
        await q.edit_message_text(f"📊 إحصائيات:\n\n👥 مستخدمين: {len(data['users'])}\n🏪 تجار: {len(data['merchants'])}\n🛍️ خدمات نقابة: {len(data['listings'])}\n🎯 مهام: {len(data['tasks'])}\n⭐ إجمالي النقاط: {sum(data['points'].values())}\n📦 طلبات: {len(data['orders'])}", reply_markup=admin_menu()); return
    if d == "admin_orders":
        if uid != ADMIN_ID: return
        txt = "📦 الطلبات:\n\n" + "\n".join([f"▫️ {o['service']} | {o['details'][:50]}" for o in data["orders"][-15:]]) if data["orders"] else "لا توجد طلبات"
        await q.edit_message_text(txt, reply_markup=admin_menu()); return
    if d == "admin_add_service":
        if uid != ADMIN_ID: return
        context.user_data["waiting_add_service"]=True
        await q.edit_message_text("أرسل: الاسم | السعر | الوصف", reply_markup=admin_menu()); return
    if d == "admin_del_service":
        if uid != ADMIN_ID: return
        kb = [[InlineKeyboardButton(f"🗑️ {s['name']}", callback_data=f"admin_del_s_{s['id']}")] for s in data["services"]]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await q.edit_message_text("اختر للحذف:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("admin_del_s_"):
        if uid != ADMIN_ID: return
        sid=int(d.split("_")[3]); data["services"]=[x for x in data["services"] if x["id"]!=sid]; save(data)
        await q.edit_message_text("✅ تم الحذف", reply_markup=admin_menu()); return
    if d == "admin_add_offer":
        if uid != ADMIN_ID: return
        context.user_data["waiting_add_offer"]=True
        await q.edit_message_text("أرسل نص العرض:", reply_markup=admin_menu()); return
    if d == "admin_add_task":
        if uid != ADMIN_ID: return
        context.user_data["waiting_add_task"]=True
        await q.edit_message_text("🎯 إضافة مهمة\n\nأرسل: العنوان | الوصف | النقاط", reply_markup=admin_menu()); return
    if d == "admin_review_tasks":
        if uid != ADMIN_ID: return
        pending = [s for s in data["submissions"] if s["status"]=="⏳ قيد المراجعة"]
        if not pending:
            await q.edit_message_text("لا توجد إثباتات معلقة", reply_markup=admin_menu()); return
        kb = [[InlineKeyboardButton(f"{s['task_title']} - {s['user_name']}", callback_data=f"review_sub_{s['id']}")] for s in pending]
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await q.edit_message_text("📝 إثباتات معلقة:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("review_sub_"):
        if uid != ADMIN_ID: return
        sid=int(d.split("_")[2]); s=next((x for x in data["submissions"] if x["id"]==sid),None)
        if s:
            kb = [[InlineKeyboardButton("✅ قبول + اعط النقاط", callback_data=f"approve_sub_{sid}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_sub_{sid}")],[InlineKeyboardButton("🔙 رجوع", callback_data="admin_review_tasks")]]
            await q.edit_message_text(f"📝 إثبات مهمة:\n\n🎯 المهمة: {s['task_title']}\n👤 المستخدم: {s['user_name']} (@{s['username']})\n⭐ النقاط: {s['points']}\n📝 الإثبات: {s['proof']}", reply_markup=InlineKeyboardMarkup(kb))
        return
    if d.startswith("approve_sub_"):
        if uid != ADMIN_ID: return
        sid=int(d.split("_")[2]); s=next((x for x in data["submissions"] if x["id"]==sid),None)
        if s and s["status"]=="⏳ قيد المراجعة":
            s["status"]="✅ مقبول"; add_pts(s["user_id"], s["points"])
            try: await context.bot.send_message(s["user_id"], f"🎉 تم قبول إثباتك!\n🎯 المهمة: {s['task_title']}\n⭐ حصلت على {s['points']} نقطة\n📊 رصيدك الآن: {pts(s['user_id'])}")
            except: pass
            await q.edit_message_text(f"✅ تم القبول واعطاء {s['points']} نقطة", reply_markup=admin_menu())
        return
    if d.startswith("reject_sub_"):
        if uid != ADMIN_ID: return
        sid=int(d.split("_")[2]); s=next((x for x in data["submissions"] if x["id"]==sid),None)
        if s:
            s["status"]="❌ مرفوض"; save(data)
            try: await context.bot.send_message(s["user_id"], f"❌ تم رفض إثبات مهمة: {s['task_title']}")
            except: pass
            await q.edit_message_text("❌ تم الرفض", reply_markup=admin_menu())
        return
    if d == "admin_listings":
        if uid != ADMIN_ID: return
        txt = "🏛️ خدمات التجار:\n\n" + "\n".join([f"▫️ {x['name']} - {x['shop']} - {x['price']}" for x in data["listings"]]) if data["listings"] else "لا توجد"
        await q.edit_message_text(txt, reply_markup=admin_menu()); return
    if d == "admin_broadcast":
        if uid != ADMIN_ID: return
        context.user_data["waiting_broadcast"]=True
        await q.edit_message_text("📣 أرسل رسالة البث:", reply_markup=admin_menu()); return

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    txt = update.message.text or ""
    ud = context.user_data
    uname = update.message.from_user.username or ""
    fname = update.message.from_user.first_name or ""
    if ud.get("waiting_merchant"):
        ud.pop("waiting_merchant")
        try:
            name, shop = [x.strip() for x in txt.split("|")]
            data["merchants"][str(uid)] = {"name": name, "shop_name": shop, "sales": 0}
            save(data)
            await update.message.reply_text(f"🎉 مبروك! صرت تاجر في النقابة\n🏪 متجرك: {shop}")
        except:
            await update.message.reply_text("❌ خطأ، أرسل: اسمك | اسم متجرك")
        return
    if ud.get("waiting_listing"):
        ud.pop("waiting_listing")
        try:
            name, price, desc = [x.strip() for x in txt.split("|")]
            m = data["merchants"][str(uid)]
            data["listings"].append({"id": data["next_listing_id"], "seller_id": uid, "shop": m["shop_name"], "name": name, "price": price, "desc": desc, "active": True})
            data["next_listing_id"]+=1; save(data)
            await update.message.reply_text(f"✅ تم نشر خدمتك في متجر النقابة: {name} - {price}")
        except:
            await update.message.reply_text("❌ خطأ، أرسل: الاسم | السعر | الوصف")
        return
    if ud.get("waiting_buy_listing"):
        listing = ud.pop("waiting_buy_listing")
        data["orders"].append({"user_id": uid, "service": f"[نقابة] {listing['name']} من {listing['shop']}", "details": txt, "status": "⏳ قيد المراجعة"})
        if str(listing["seller_id"]) in data["merchants"]:
            data["merchants"][str(listing["seller_id"])]["sales"]+=1
        save(data)
        await update.message.reply_text(f"✅ تم إرسال طلبك للتاجر\n🏪 {listing['shop']}\n💎 {listing['name']}")
        try: await context.bot.send_message(listing["seller_id"], f"🔔 طلب جديد من النقابة!\n\n💎 خدمتك: {listing['name']}\n👤 الزبون: {fname} (@{uname})\n📝 {txt}")
        except: pass
        return
    if ud.get("waiting_task_proof"):
        tid = ud.pop("waiting_task_proof")
        t = next((x for x in data["tasks"] if x["id"]==tid), None)
        if t:
            data["submissions"].append({"id": data["next_sub_id"], "user_id": uid, "user_name": fname, "username": uname, "task_title": t["title"], "points": t["points"], "proof": txt, "status": "⏳ قيد المراجعة"})
            data["next_sub_id"]+=1; save(data)
            await update.message.reply_text(f"✅ تم استلام إثباتك لمهمة: {t['title']}\n\n⏳ بنراجعه ونعطيك {t['points']} ⭐")
            try: await context.bot.send_message(ADMIN_ID, f"📝 إثبات مهمة جديد!\n🎯 {t['title']}\n👤 {fname} (@{uname})\n📝 {txt}")
            except: pass
        return
    if uid==ADMIN_ID and ud.get("waiting_broadcast"):
        ud.pop("waiting_broadcast"); sent=0
        for u in data["users"]:
            try: await context.bot.send_message(u, f"📣 من {SHOP_NAME}:\n\n{txt}"); sent+=1
            except: pass
        await update.message.reply_text(f"✅ تم البث لـ {sent} شخص"); return
    if uid==ADMIN_ID and ud.get("waiting_add_service"):
        ud.pop("waiting_add_service")
        try:
            name, price, desc = [x.strip() for x in txt.split("|")]
            data["services"].append({"id": data["next_service_id"], "name": name, "price": price, "desc": desc}); data["next_service_id"]+=1; save(data)
            await update.message.reply_text(f"✅ تم إضافة {name}")
        except: await update.message.reply_text("❌ أرسل: الاسم | السعر | الوصف")
        return
    if uid==ADMIN_ID and ud.get("waiting_add_offer"):
        ud.pop("waiting_add_offer"); data["offers"].append(txt); save(data)
        await update.message.reply_text("✅ تم إضافة العرض"); return
    if uid==ADMIN_ID and ud.get("waiting_add_task"):
        ud.pop("waiting_add_task")
        try:
            title, desc, pts_val = [x.strip() for x in txt.split("|")]
            data["tasks"].append({"id": data["next_task_id"], "title": title, "desc": desc, "points": int(pts_val), "active": True})
            data["next_task_id"]+=1; save(data)
            await update.message.reply_text(f"✅ تم إضافة مهمة: {title} - {pts_val} ⭐")
        except: await update.message.reply_text("❌ أرسل: العنوان | الوصف | النقاط")
        return
    if ud.get("waiting_order"):
        service = ud.pop("waiting_order")
        data["orders"].append({"user_id": uid, "service": service, "details": txt, "status": "⏳ قيد المراجعة"}); save(data)
        await update.message.reply_text(f"✅ تم استلام طلبك: {service}\nبنرد عليك قريب 👑")
        try: await context.bot.send_message(ADMIN_ID, f"🔔 طلب جديد!\n💎 {service}\n👤 {fname} (@{uname})\n📝 {txt}")
        except: pass
        return
    await update.message.reply_text("أهلاً بك في Pro Max 👑\nاضغط /start للقائمة")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ للادمن فقط"); return
    await update.message.reply_text("👑 لوحة تحكم Pro Max", reply_markup=admin_menu())

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("بوت Pro Max - النقابة + المهام شغال...")
    app.run_polling()
