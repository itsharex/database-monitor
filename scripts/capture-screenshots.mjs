/**
 * 自动截图脚本 - 用于公众号文章
 */
import { chromium } from 'playwright'
import { mkdir } from 'fs/promises'
import path from 'path'

const BASE = 'http://localhost:8088'
const OUT = path.resolve('docs/wechat-article/images')

async function main() {
  await mkdir(OUT, { recursive: true })
  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()

  // 登录页
  await page.goto(`${BASE}/login`)
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(OUT, '01-login.png'), fullPage: false })

  // 登录
  await page.fill('input[placeholder="用户名"]', 'admin')
  await page.fill('input[placeholder="密码"]', 'admin123')
  await page.click('button:has-text("登")')
  await page.waitForURL('**/')
  await page.waitForTimeout(3000)

  // 大屏全貌
  await page.screenshot({ path: path.join(OUT, '02-dashboard.png'), fullPage: false })

  // 全屏模式
  await page.click('button[title="全屏"]')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, '03-dashboard-fullscreen.png'), fullPage: false })
  await page.click('button[title="退出全屏"]')
  await page.waitForTimeout(500)

  // 浅色主题
  await page.click('button[title="切换浅色模式"]')
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(OUT, '04-dashboard-light.png'), fullPage: false })
  await page.click('button[title="切换深色模式"]')
  await page.waitForTimeout(800)

  // 管理页 - 实例
  await page.click('button:has-text("管理")')
  await page.waitForURL('**/manage')
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(OUT, '05-manage-instances.png'), fullPage: true })

  // 告警规则
  await page.click('.el-tabs__item:has-text("告警规则")')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, '06-manage-rules.png'), fullPage: true })

  // 通知渠道
  await page.click('.el-tabs__item:has-text("通知渠道")')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, '07-manage-channels.png'), fullPage: true })

  // 采集日志
  await page.click('.el-tabs__item:has-text("采集日志")')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, '08-manage-logs.png'), fullPage: true })

  // 数据导出
  await page.click('.el-tabs__item:has-text("数据导出")')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, '09-manage-export.png'), fullPage: true })

  // 添加实例弹窗
  await page.click('.el-tabs__item:has-text("数据库实例")')
  await page.waitForTimeout(500)
  await page.click('button:has-text("添加实例")')
  await page.waitForTimeout(800)
  await page.screenshot({ path: path.join(OUT, '10-add-instance-dialog.png'), fullPage: false })
  await page.click('button:has-text("取消")')
  await page.waitForTimeout(500)

  // 实例详情
  await page.goto(`${BASE}/`)
  await page.waitForTimeout(2000)
  // 双击第一个实例或导航到详情
  const instanceId = 4 // local-mysql
  await page.goto(`${BASE}/instance/${instanceId}`)
  await page.waitForTimeout(2500)
  await page.screenshot({ path: path.join(OUT, '11-instance-detail.png'), fullPage: true })

  // 返回大屏 - 历史回放区域
  await page.goto(`${BASE}/`)
  await page.waitForTimeout(2000)
  await page.click('button:has-text("历史回放")')
  await page.waitForTimeout(800)
  await page.screenshot({ path: path.join(OUT, '12-history-replay.png'), fullPage: false })

  await browser.close()
  console.log('Screenshots saved to', OUT)
}

main().catch((e) => { console.error(e); process.exit(1) })
